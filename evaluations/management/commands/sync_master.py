import time
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand,CommandError
from evaluations.models import AcademicSession
from evaluations.google_sync import sync_google
from evaluations.services import role
class Command(BaseCommand):
    help='Read the existing Google master workbook once or poll it without modifying n8n.'
    def add_arguments(self,parser):
        parser.add_argument('--session',required=True)
        parser.add_argument('--coordinator',required=True)
        parser.add_argument('--watch',action='store_true')
        parser.add_argument('--interval',type=int,default=60)
    def handle(self,*args,**options):
        user=get_user_model().objects.filter(username=options['coordinator']).first()
        if role(user)!='coordinator':raise CommandError('An authorized Coordinator identity is required.')
        try:session=AcademicSession.objects.get(label=options['session'])
        except AcademicSession.DoesNotExist:raise CommandError('Academic session not found.')
        if options['interval']<30:raise CommandError('Use an interval of at least 30 seconds.')
        while True:
            try:
                result=sync_google(session,user)
                self.stdout.write(f"Master read: {result['accepted']} refreshed, {result['unchanged']} unchanged, {result['held']} protected, {len(result['issues'])} issues. Review Import history.")
            except Exception as error:
                if not options['watch']:raise CommandError('Google master read failed. Check the private server credential and workbook permissions.') from error
                self.stderr.write('Google master read failed; retrying next interval. Check connection and audit records.')
            if not options['watch']:break
            try:time.sleep(options['interval'])
            except KeyboardInterrupt:break
