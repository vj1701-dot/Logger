import random
import string
from datetime import datetime
from .sheets_utils import get_tasks

def generate_uid():
    # Use date-based prefix (e.g., 2107 for July 21)
    date_prefix = datetime.utcnow().strftime("%d%m")
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    uid = f"{date_prefix}{suffix}"

    # Check for collision with existing UIDs
    existing_uids = {row[1] for row in get_tasks() if len(row) > 1}
    while uid in existing_uids:
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        uid = f"{date_prefix}{suffix}"

    return uid
