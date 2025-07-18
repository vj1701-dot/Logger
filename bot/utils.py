import random
import string
import secrets

def generate_uid():
    prefix = ''.join(random.choices(string.ascii_uppercase, k=2))
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}{suffix}"

print(secrets.token_urlsafe(32))
