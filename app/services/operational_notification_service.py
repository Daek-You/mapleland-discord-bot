"""Operational Discord notifications for deployments and process status."""

from __future__ import annotations

import logging

import httpx

from app.config import get_app_env, get_bot_name, get_discord_alert_webhook_url

logger = logging.getLogger(__name__)
DEFAULT_NOTIFICATION_TIMEOUT_SECONDS = 5.0


def send_operational_notification(
    message: str,
    webhook_url: str | None = None,
    timeout_seconds: float = DEFAULT_NOTIFICATION_TIMEOUT_SECONDS,
) -> bool:
    """Send an operational notification through a Discord webhook."""
    target_webhook_url = webhook_url or get_discord_alert_webhook_url()
    if not target_webhook_url:
        logger.info("Operational Discord webhook is not set. Skipping notification.")
        return False

    payload = {"content": _format_operational_message(message)}
    try:
        response = httpx.post(
            target_webhook_url,
            json=payload,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        logger.error("Failed to send operational Discord notification.", exc_info=True)
        return False

    return True


def _format_operational_message(message: str) -> str:
    return f"[{get_app_env()}] {get_bot_name()}: {message}"
