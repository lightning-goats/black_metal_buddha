from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_env: str
    public_base_url: str
    database_url: str
    phase1_api_enabled: bool
    square_environment: str
    square_api_version: str
    square_access_token: str | None
    square_location_id: str | None
    square_webhook_signature_key: str | None
    square_webhook_notification_url: str | None
    printful_token: str | None
    printful_store_id: str | None
    printful_mode: str
    printful_webhook_secret_key: str | None
    printful_webhook_public_key: str | None
    phase0_5_approved: bool
    email_mode: str
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    email_from: str | None
    printful_confirm_enabled: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_env=os.getenv("APP_ENV", "development"),
            public_base_url=os.getenv("PUBLIC_BASE_URL", "https://blackmetalbuddha.com").rstrip("/"),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./black_metal_buddha.db"),
            phase1_api_enabled=_bool("PHASE1_API_ENABLED", False),
            square_environment=os.getenv("SQUARE_ENVIRONMENT", "sandbox").lower(),
            square_api_version=os.getenv("SQUARE_API_VERSION", "2026-09-16"),
            square_access_token=os.getenv("SQUARE_ACCESS_TOKEN"),
            square_location_id=os.getenv("SQUARE_LOCATION_ID"),
            square_webhook_signature_key=os.getenv("SQUARE_WEBHOOK_SIGNATURE_KEY"),
            square_webhook_notification_url=os.getenv("SQUARE_WEBHOOK_NOTIFICATION_URL"),
            printful_token=os.getenv("PRINTFUL_TOKEN"),
            printful_store_id=os.getenv("PRINTFUL_STORE_ID"),
            printful_mode=os.getenv("PRINTFUL_MODE", "disabled").lower(),
            printful_webhook_secret_key=os.getenv("PRINTFUL_WEBHOOK_SECRET_KEY"),
            printful_webhook_public_key=os.getenv("PRINTFUL_WEBHOOK_PUBLIC_KEY"),
            phase0_5_approved=_bool("PHASE0_5_APPROVED", False),
            email_mode=os.getenv("EMAIL_MODE", "disabled").lower(),
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME"),
            smtp_password=os.getenv("SMTP_PASSWORD"),
            email_from=os.getenv("EMAIL_FROM"),
            printful_confirm_enabled=_bool("PRINTFUL_CONFIRM_ENABLED", False),
        )

    @property
    def square_api_base(self) -> str:
        if self.square_environment == "production":
            return "https://connect.squareup.com"
        return "https://connect.squareupsandbox.com"

    def validate_safety(self) -> None:
        if self.printful_mode not in {"disabled", "draft", "production"}:
            raise ValueError("PRINTFUL_MODE must be disabled, draft, or production")
        if self.email_mode not in {"disabled", "console", "smtp"}:
            raise ValueError("EMAIL_MODE must be disabled, console, or smtp")
        if self.email_mode == "smtp" and (not self.smtp_host or not self.email_from):
            raise ValueError("SMTP_HOST and EMAIL_FROM are required when EMAIL_MODE=smtp")
        if self.printful_mode == "production":
            if not self.phase0_5_approved:
                raise ValueError("Production Printful fulfillment requires PHASE0_5_APPROVED=true")
            if not self.printful_confirm_enabled:
                raise ValueError("Production Printful fulfillment requires PRINTFUL_CONFIRM_ENABLED=true")
        if self.app_env == "production" and self.phase1_api_enabled:
            raise ValueError(
                "Production checkout is intentionally blocked in the Phase 1 foundation"
            )


settings = Settings.from_env()
settings.validate_safety()
