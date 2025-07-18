# Unified Telegram Bot + Dashboard (Single Cloud Run Service)

This app runs both:
- A Telegram bot at `/webhook`
- A Flask dashboard at `/dashboard`

## Deployment

- Deploy via Cloud Run using Dockerfile
- Inject these secrets via Secret Manager or env:
  - TELEGRAM_BOT_TOKEN
  - DASHBOARD_PASS
  - ADMIN_IDS
  - DASHBOARD_URL (optional)

## Usage

- POST Telegram updates to `/webhook`
- Access dashboard at `/dashboard?password=...`
