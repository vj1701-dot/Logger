import random
import string

def generate_uid():
    return ''.join(random.choices(string.ascii_uppercase, k=2)) + str(random.randint(1000, 9999))
