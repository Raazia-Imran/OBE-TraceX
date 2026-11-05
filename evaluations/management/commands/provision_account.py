from getpass import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from evaluations.models import Profile
class Command(BaseCommand):
    help = 'Create an authorized account interactively. No default or generated shared password.'
    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('--role', choices=['coordinator', 'hod'], required=True)
        parser.add_argument('--name', default='')
    def handle(self, *args, **options):
        username = options['username']
        if get_user_model().objects.filter(username=username).exists(): raise CommandError('Account already exists. Use Django changepassword for recovery.')
        password, confirm = getpass('New password: '), getpass('Repeat password: ')
        if password != confirm: raise CommandError('Passwords do not match.')
        user = get_user_model()(username=username, first_name=options['name'])
        try: validate_password(password, user)
        except Exception as error: raise CommandError(str(error)) from error
        with transaction.atomic():
            user.set_password(password)
            user.save()
            Profile.objects.create(user=user, role=options['role'])
        self.stdout.write(self.style.SUCCESS('Account created. Enroll MFA before production use.'))
