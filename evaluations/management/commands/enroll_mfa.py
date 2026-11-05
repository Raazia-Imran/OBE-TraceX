from getpass import getpass
from urllib.parse import quote
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from evaluations.mfa import cipher, generate_secret, verify
from evaluations.services import audit
class Command(BaseCommand):
    help = 'Enroll TOTP locally with the account owner. Run only in an authorized private terminal.'
    def add_arguments(self, parser): parser.add_argument('username')
    def handle(self, *args, **options):
        user = get_user_model().objects.get(username=options['username'])
        profile = user.profile
        if profile.mfa_secret: raise CommandError('Already enrolled. Recovery requires the documented IT process.')
        if not user.check_password(getpass('Current password: ')): raise CommandError('Authentication failed.')
        secret = generate_secret()
        self.stdout.write('Add this secret to your authenticator privately. Do not share or screenshot it:')
        self.stdout.write(secret)
        self.stdout.write('otpauth://totp/' + quote('OBE-TraceX:' + user.username) + '?secret=' + secret + '&issuer=OBE-TraceX')
        profile.mfa_secret = cipher().encrypt(secret.encode()).decode()
        if not verify(profile, getpass('Authenticator verification code: ').strip()): raise CommandError('Verification failed; enrollment not saved.')
        profile.save(update_fields=['mfa_secret'])
        audit(user, 'account.mfa_enrolled', user.pk)
        self.stdout.write(self.style.SUCCESS('MFA enrolled. Store account recovery instructions with university IT.'))
