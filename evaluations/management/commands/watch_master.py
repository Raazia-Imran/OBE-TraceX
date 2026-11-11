import time
from datetime import timedelta
from django.core.management.base import BaseCommand,CommandError
from django.contrib.auth import get_user_model
from django.db import transaction,close_old_connections
from django.utils import timezone
from evaluations.models import AcademicSession,SyncState,MasterRecord
from evaluations.services import role
from evaluations.google_sync import sync_google
class Command(BaseCommand):
    help='Read the configured master workbook on a controlled interval; never write source formulas.'
    def add_arguments(self,p):
        p.add_argument('--session',type=int,required=True);p.add_argument('--coordinator',required=True)
        p.add_argument('--interval',type=int,default=60);p.add_argument('--once',action='store_true')
    def handle(self,*args,**options):
        session=AcademicSession.objects.get(pk=options['session']);actor=get_user_model().objects.get(username=options['coordinator'])
        if role(actor)!='coordinator':raise CommandError('A Coordinator account is required.')
        if session.course_code=='REHEARSAL' or MasterRecord.objects.filter(student__session=session,payload__source='faculty_reference_workbook').exists():
            raise CommandError('Use a dedicated live session; saved faculty/rehearsal data is protected.')
        while True:
            close_old_connections();now=timezone.now()
            with transaction.atomic():
                state,_=SyncState.objects.get_or_create(session=session)
                state=SyncState.objects.select_for_update().get(pk=state.pk)
                if state.running_until and state.running_until>now:raise CommandError('Another reader holds this session lease.')
                state.running_until=now+timedelta(seconds=180);state.attempted_at=now;state.save()
            try:
                summary=sync_google(session,actor)
                SyncState.objects.filter(pk=state.pk).update(succeeded_at=timezone.now(),error='',summary=summary,running_until=None)
                self.stdout.write(f'Read completed: {summary["accepted"]} updated; {len(summary["issues"])} validation issues.')
            except Exception:
                SyncState.objects.filter(pk=state.pk).update(error='Google read failed. Check n8n, account authorization and workbook schema.',running_until=None)
                self.stderr.write('Read failed; existing portal records preserved.')
            if options['once']:break
            time.sleep(max(30,options['interval']))
