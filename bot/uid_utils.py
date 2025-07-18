import random
import string

def generate_uid():
    return ''.join(random.choices(string.ascii_uppercase, k=2)) + ''.join(random.choices(string.digits, k=4))
