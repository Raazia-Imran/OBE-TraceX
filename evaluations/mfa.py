"""TOTP with encrypted enrollment secrets and a monotonically increasing replay counter."""
import base64
import hashlib
import hmac
import os
import struct
import time
from cryptography.fernet import Fernet

def cipher():
    key = os.environ.get('OBE_MFA_KEY', '')
    if not key: raise ValueError('OBE_MFA_KEY is required for MFA enrollment and sign-in.')
    return Fernet(key.encode())

def generate_secret(): return base64.b32encode(os.urandom(20)).decode().rstrip('=')

def token(secret, counter):
    key = base64.b32decode(secret + '=' * ((8 - len(secret) % 8) % 8))
    value = hmac.new(key, struct.pack('>Q', counter), hashlib.sha1).digest()
    offset = value[-1] & 15
    code = (struct.unpack('>I', value[offset:offset+4])[0] & 0x7fffffff) % 1000000
    return str(code).zfill(6)

def verify(profile, code):
    if not code.isdigit() or len(code) != 6: return False
    secret = cipher().decrypt(profile.mfa_secret.encode()).decode()
    current = int(time.time()) // 30
    for counter in [current - 1, current, current + 1]:
        if counter > profile.mfa_counter and hmac.compare_digest(token(secret, counter), code):
            profile.mfa_counter = counter
            profile.save(update_fields=['mfa_counter'])
            return True
    return False
