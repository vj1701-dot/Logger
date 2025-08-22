# Telegram-First Maintenance Task System

A comprehensive task management system built for Google Cloud Run with Telegram as the primary interface. Features include a Telegram bot for task creation and management, a web dashboard for admins, and a Telegram Mini App for mobile access.

## 🚀 Features

### Bot-Heavy Workflow
- **Task Creation**: Send any message with text/media to create tasks with sequential UIDs (SJ0001-SJ9999+)
- **Status Management**: Interactive buttons for status changes with role-based permissions
- **Assignment**: Multi-assignee support via admin commands
- **Notes**: Add notes via replies or commands, including audio/media attachments
- **Notifications**: Real-time updates for assignments, status changes, and completions

### Admin Dashboard (Next.js)
- **Task Management**: View, edit, filter, and search tasks with rich media galleries
- **User Management**: Full CRUD operations on users with role management
- **Data Export**: CSV export functionality for users and audit trails
- **Media Management**: View and delete media files with automatic retention

### Telegram Mini App
- **Read-Only Access**: Mobile-optimized view of assigned tasks
- **Responsive Design**: Follows Telegram's light/dark theme
- **Native Integration**: Seamless authentication via Telegram WebApp

### Cloud-Native Storage
- **Google Cloud Storage**: All data stored as JSON in a single private bucket
- **Sequential UIDs**: Atomic counter using GCS conditional writes
- **Index Markers**: Fast queries via zero-byte marker files
- **Media Retention**: Automatic deletion 7 days after task completion
- **Audit Logging**: Comprehensive audit trail for all admin actions

## 📁 Project Structure

```
.
├── src/                          # Backend Python code
│   ├── api/                      # FastAPI routes
│   ├── auth/                     # JWT authentication & middleware
│   ├── bot/                      # Telegram bot handlers
│   ├── models/                   # Data models (Task, User)
│   ├── services/                 # Business logic services
│   ├── storage/                  # GCS client
│   └── config.py                 # Configuration settings
├── dashboard/                    # Next.js admin dashboard
│   ├── app/                      # Next.js 14 app directory
│   ├── components/               # React components
│   └── lib/                      # Auth & API utilities
├── miniapp/                      # Telegram Mini App (Vite + React)
│   ├── src/
│   │   ├── components/           # Mini app components
│   │   └── services/             # Telegram & API services
├── main.py                       # FastAPI application entry point
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Multi-stage build configuration
└── README.md                     # This file
```

## 🗄️ Data Storage Layout (GCS)

```
bucket-name/
├── counters/
│   └── uid.seq                   # Sequential UID counter
├── tasks/
│   └── {UID}.json               # Task documents
├── users/
│   └── {telegramId}.json        # User profiles
├── index/
│   ├── status/{status}/{UID}    # Status-based task indices
│   └── assignee/{telegramId}/{UID} # Assignee-based indices
├── media/
│   └── {UID}/                   # Task media files
├── audit/
│   └── YYYY/MM/DD/*.jsonl       # Daily audit logs
```

## 🔐 Authentication & Authorization

### JWT-Based Authentication
- **Magic Link Flow**: Secure login via Telegram DM verification
- **Token Management**: 60-minute JWT tokens with automatic refresh
- **Role-Based Access**: User vs Admin permissions

### Telegram Mini App Authentication
- **initData Validation**: Secure HMAC verification of Telegram WebApp data
- **Seamless Integration**: No additional login required

## 🚀 Deployment

### Prerequisites

1. **Google Cloud Project Setup**
   ```bash
   # Enable required APIs
   gcloud services enable run.googleapis.com
   gcloud services enable storage.googleapis.com
   ```

2. **Create GCS Bucket**
   ```bash
   gsutil mb gs://your-maintenance-bucket
   gsutil iam ch serviceAccount:your-service-account@project.iam.gserviceaccount.com:objectAdmin gs://your-maintenance-bucket
   ```

3. **Telegram Bot Setup**
   - Create bot via [@BotFather](https://t.me/BotFather)
   - Set webhook: `https://your-app.run.app/webhook/telegram`
   - Configure Mini App URL: `https://your-app.run.app/miniapp/`

### Environment Variables

Set these in Cloud Run:

```bash
# Core Configuration
BUCKET_NAME=your-maintenance-bucket
TELEGRAM_BOT_TOKEN=your_bot_token
JWT_SIGNING_KEY=your_jwt_secret_key_change_in_production
APP_BASE_URL=https://your-app.run.app

# Timing Configuration
JWT_TTL_MIN=60
MAGIC_LINK_TTL_MIN=10

# Cron Security
CRON_KEY=your_secure_cron_key

# Optional Basic Auth Fallback
ADMIN_USER=admin
ADMIN_PASS=secure_password

# Environment
ENVIRONMENT=production
```

### Deploy to Cloud Run

1. **Build and Deploy**
   ```bash
   # Clone the repository
   git clone your-repo
   cd Logger
   
   # Build and deploy
   gcloud run deploy maintenance-task-system \
     --source . \
     --platform managed \
     --region us-central1 \
     --memory 1Gi \
     --cpu 1 \
     --max-instances 10 \
     --allow-unauthenticated \
     --set-env-vars BUCKET_NAME=your-bucket,TELEGRAM_BOT_TOKEN=your-token,...
   ```

2. **Set up Scheduled Jobs**
   ```bash
   # Create Cloud Scheduler job for media retention
   gcloud scheduler jobs create http media-retention-job \
     --schedule="0 2 * * *" \
     --uri="https://your-app.run.app/api/cron/media-retention" \
     --http-method=GET \
     --headers="X-CRON-KEY=your_secure_cron_key"
   ```

3. **Configure Bot Webhook**
   ```bash
   curl -X POST "https://api.telegram.org/bot{BOT_TOKEN}/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-app.run.app/webhook/telegram"}'
   ```

## 🔧 Development Setup

### Backend Development
```bash
# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export BUCKET_NAME=dev-bucket
export TELEGRAM_BOT_TOKEN=your-dev-token
# ... other vars

# Run development server
uvicorn main:app --reload --port 8080
```

### Dashboard Development
```bash
cd dashboard
npm install
npm run dev  # Runs on port 3000
```

### Mini App Development
```bash
cd miniapp
npm install
npm run dev  # Runs on port 3001
```

## 📚 API Documentation

### Authentication Endpoints
- `POST /api/auth/login` - Request magic link
- `GET /api/auth/magic-link` - Verify magic link and get JWT
- `POST /api/miniapp/validate` - Validate Telegram Mini App data

### Task Management
- `GET /api/tasks` - List tasks with filters
- `GET /api/tasks/{uid}` - Get task details
- `PATCH /api/tasks/{uid}` - Update task (admin)
- `POST /api/tasks/{uid}/status` - Change status (admin)
- `POST /api/tasks/{uid}/assignees` - Manage assignees (admin)
- `POST /api/tasks/{uid}/note` - Add note (admin)

### User Management (Admin Only)
- `GET /api/users` - List all users
- `PATCH /api/users/{telegram_id}` - Update user
- `POST /api/users` - Create user stub
- `GET /api/users/export` - Export users CSV

### Media & Cron
- `GET /api/media/{uid}/{filename}` - Stream media file
- `DELETE /api/media/{uid}/{filename}` - Delete media (admin)
- `GET /api/cron/media-retention` - Media cleanup job

## 🤖 Telegram Bot Commands

### User Commands
- `/start` - Welcome message and instructions
- `/status {UID}` - View task status with action buttons
- `/note {UID} {text}` - Add note to task
- Reply to task messages to add notes

### Admin Commands
- `/assign {UID} {telegram_id}` - Assign user to task
- All user commands plus admin-only status changes

### Interactive Features
- **Status Buttons**: Quick status changes via inline keyboards
- **Media Support**: Photos, videos, audio, documents, voice messages
- **Notifications**: Assignment alerts, status change confirmations

## 🔒 Security Features

- **No Service Account Keys**: Uses Cloud Run default credentials
- **Private Bucket**: All access through authenticated backend
- **JWT Authentication**: Secure token-based auth with expiration
- **HMAC Verification**: Telegram WebApp data validation
- **Role-Based Access**: Granular permissions for users vs admins
- **Audit Logging**: Complete trail of admin actions
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: Built-in through Cloud Run

## 📊 Monitoring & Observability

### Built-in Features
- **Health Checks**: `/health` endpoint for monitoring
- **Structured Logging**: JSON logs for Cloud Logging
- **Error Handling**: Comprehensive exception handling
- **Audit Trail**: All admin actions logged with timestamps

### Recommended Monitoring
```bash
# Set up Cloud Monitoring alerts
gcloud alpha monitoring channels create \
  --notification-channel-config-from-file=alert-config.yaml
```

## 🧪 Testing

### Unit Tests
```bash
# Run backend tests
python -m pytest tests/

# Run dashboard tests
cd dashboard && npm test

# Run mini app tests
cd miniapp && npm test
```

### Integration Tests
```bash
# Test webhook endpoint
curl -X POST https://your-app.run.app/webhook/telegram \
  -H "Content-Type: application/json" \
  -d '{"update_id": 1, "message": {...}}'

# Test authentication flow
curl -X POST https://your-app.run.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"telegram_id": 12345}'
```

## 🚨 Troubleshooting

### Common Issues

1. **Bot Not Responding**
   - Check webhook URL and SSL certificate
   - Verify TELEGRAM_BOT_TOKEN is correct
   - Check Cloud Run logs for errors

2. **Authentication Failures**
   - Verify JWT_SIGNING_KEY is set
   - Check token expiration settings
   - Ensure user exists in system

3. **Storage Issues**
   - Verify bucket permissions
   - Check GCS client credentials
   - Monitor bucket quotas

4. **Performance Issues**
   - Scale Cloud Run instances
   - Optimize media file sizes
   - Use CDN for static assets

### Debug Commands
```bash
# Check Cloud Run logs
gcloud run services logs read maintenance-task-system

# Test bucket access
gsutil ls gs://your-bucket/

# Verify webhook
curl -X GET "https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
```

## 📄 License

This project is provided as-is for educational and internal use purposes.

## 🤝 Contributing

This system is designed to be self-contained and deployment-ready. For modifications:

1. Follow the existing code structure
2. Maintain security best practices
3. Update documentation accordingly
4. Test thoroughly before deployment

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review Cloud Run and GCS logs
3. Verify environment variables and permissions
4. Test with minimal reproduction cases
