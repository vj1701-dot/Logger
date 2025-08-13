from googleapiclient.discovery import build
from bot.config import GOOGLE_CREDENTIALS, GOOGLE_SHEET_ID


def _sheets_service():
	return build('sheets', 'v4', credentials=GOOGLE_CREDENTIALS)


def _ensure_admins_sheet_exists():
	service = _sheets_service().spreadsheets()
	meta = service.get(spreadsheetId=GOOGLE_SHEET_ID).execute()
	for sheet in meta.get('sheets', []):
		title = sheet.get('properties', {}).get('title')
		if title == 'Admins':
			return
	# Add the 'Admins' sheet/tab
	service.batchUpdate(
		spreadsheetId=GOOGLE_SHEET_ID,
		body={
			"requests": [
				{"addSheet": {"properties": {"title": "Admins"}}}
			]
		}
	).execute()


def get_admin_ids() -> set:
	"""Return a set of admin user IDs (as strings) from the Admins sheet."""
	_ensure_admins_sheet_exists()
	vals = _sheets_service().spreadsheets().values().get(
		spreadsheetId=GOOGLE_SHEET_ID,
		range='Admins!A:A'
	).execute().get('values', [])
	return {row[0].strip() for row in vals if row and row[0].strip()}


def is_admin(user_id) -> bool:
	return str(user_id) in get_admin_ids()


def add_admin(user_id: str) -> bool:
	"""Add a user ID to the Admins sheet. Returns True if added, False if already present."""
	user_id = str(user_id)
	current = get_admin_ids()
	if user_id in current:
		return False
	_sheets_service().spreadsheets().values().append(
		spreadsheetId=GOOGLE_SHEET_ID,
		range='Admins!A:A',
		valueInputOption='RAW',
		body={'values': [[user_id]]}
	).execute()
	return True


def remove_admin(user_id: str) -> bool:
	"""Remove a user ID from Admins. Returns True if removed, False if not present."""
	user_id = str(user_id)
	current = list(get_admin_ids())
	if user_id not in current:
		return False
	filtered = [uid for uid in current if uid != user_id]
	svc = _sheets_service().spreadsheets().values()
	# Clear existing
	svc.clear(spreadsheetId=GOOGLE_SHEET_ID, range='Admins!A:A', body={}).execute()
	# Rewrite filtered
	if filtered:
		svc.update(
			spreadsheetId=GOOGLE_SHEET_ID,
			range='Admins!A1',
			valueInputOption='RAW',
			body={'values': [[uid] for uid in filtered]}
		).execute()
	return True 