import random
import string

def generate_uid():
    prefix = ''.join(random.choices(string.ascii_uppercase, k=2))
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}{suffix}"
