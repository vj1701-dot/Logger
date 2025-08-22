import os
from typing import Optional

class Settings:
    # GCS Configuration
    BUCKET_NAME: str = os.getenv("BUCKET_NAME", "project-maintenance")
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # JWT Configuration
    JWT_SIGNING_KEY: str = os.getenv("JWT_SIGNING_KEY", "change-me-in-production")
    JWT_TTL_MIN: int = int(os.getenv("JWT_TTL_MIN", "60"))
    
    # Application Configuration
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "https://your-app.run.app")
    
    # Magic Link Configuration
    MAGIC_LINK_TTL_MIN: int = int(os.getenv("MAGIC_LINK_TTL_MIN", "10"))
    
    # Cron Configuration
    CRON_KEY: str = os.getenv("CRON_KEY", "change-me-in-production")
    
    # Optional Basic Auth Fallback
    ADMIN_USER: Optional[str] = os.getenv("ADMIN_USER")
    ADMIN_PASS: Optional[str] = os.getenv("ADMIN_PASS")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"
    
    def validate(self):
        """Validate required settings"""
        required = [
            ("BUCKET_NAME", self.BUCKET_NAME),
            ("TELEGRAM_BOT_TOKEN", self.TELEGRAM_BOT_TOKEN),
            ("JWT_SIGNING_KEY", self.JWT_SIGNING_KEY),
            ("APP_BASE_URL", self.APP_BASE_URL),
            ("CRON_KEY", self.CRON_KEY),
        ]
        
        missing = [name for name, value in required if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

settings = Settings()

# Validate settings on import
if not settings.is_development:
    settings.validate()