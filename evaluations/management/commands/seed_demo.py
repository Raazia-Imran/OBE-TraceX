"""A repeatable synthetic walkthrough, never a production-data bootstrap."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from evaluations.models import AcademicSession, Assignment, ProjectGroup, Student
from evaluations.rubrics import RUBRICS
from evaluations.services import audit, receive_evaluation, role

class Command(BaseCommand):
    help = 'Add a clearly labelled synthetic demo session to the local development database.'
    def add_arguments(self, parser):
        parser.add_argument('--coordinator', required=True)
        parser.add_argument('--confirm-synthetic', action='store_true', required=True)
    @transaction.atomic
    def handle(self, *args, **options):
        if settings.PRODUCTION: raise CommandError('Synthetic seeding is disabled in production.')
        user=get_user_model().objects.filter(username=options['coordinator']).first()
        if role(user) != 'coordinator': raise CommandError('Create a Coordinator account first.')
        if AcademicSession.objects.filter(label='DEMO ONLY — Synthetic session').exists():
            self.stdout.write('The demo already exists. Its reviews and approvals have been preserved.'); return
        session=AcademicSession.objects.create(label='DEMO ONLY — Synthetic session',course_code='DEMO-401')
        for group_index, size in [(1,4),(2,3)]:
            group=ProjectGroup.objects.create(session=session,project_id=f'DEMO-{group_index:03d}',
                title='Synthetic evaluation walkthrough' if group_index==1 else 'Incomplete assessment example', expected_members=size)
            for i in range(size):
                seat=f'SE-99{group_index}{i+1:02d}'
                student=Student.objects.create(group=group,session=session,seat=seat,name=f'Sample Student {group_index}-{i+1}')
                for stage,rubric in RUBRICS.items():
                    evaluators=['supervisor@example.test'] if stage in ['D2','D4'] else ['internal@example.test','external@example.test']
                    for evaluator_index,email in enumerate(evaluators):
                        Assignment.objects.create(student=student,stage=stage,evaluator=email)
                        if group_index==2 and stage not in ['D1','D2']: continue
                        scores=[100 if evaluator_index==0 else 75]*len(rubric['maxima'])
                        if stage=='D4': scores[-1]=100 if i%2==0 else 0
                        receive_evaluation({'session':session.label,'seat':seat,'stage':stage,'evaluator':email,
                            'source_id':f'demo:{seat}:{stage}:{email}','percentages':scores,'comments':'Synthetic demonstration only.'},user)
        audit(user,'demo.created',session.pk,{'synthetic':True})
        self.stdout.write(self.style.SUCCESS('Demo created: 7 synthetic students in 2 groups.'))
        self.stdout.write('No accounts, real workbooks, Google Forms or n8n workflows were changed.')
        self.stdout.write('Sign in as HOD to review the demo policy, then use Coordinator to freeze stages.')
