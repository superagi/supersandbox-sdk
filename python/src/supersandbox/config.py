"""Client configuration model with environment-variable fallback."""

from __future__ import annotations

import os

from pydantic import BaseModel, Field


class SandboxConfig(BaseModel):
    """Configuration for the SuperSandbox client.

    Values are read from constructor arguments first, then environment variables.

    Environment variables:
        SUPERSANDBOX_API_KEY   — API key
        SUPERSANDBOX_BASE_URL  — API base URL (default: https://sandbox.superagii.com)
        SUPERSANDBOX_TIMEOUT   — Request timeout in seconds (default: 60)
    """

    api_key: str = Field(
        default_factory=lambda: os.environ.get("SUPERSANDBOX_API_KEY", "")
    )
    base_url: str = Field(
        default_factory=lambda: os.environ.get(
            "SUPERSANDBOX_BASE_URL", "https://sandbox.superagii.com"
        )
    )
    timeout: float = Field(
        default_factory=lambda: float(os.environ.get("SUPERSANDBOX_TIMEOUT", "60"))
    )
