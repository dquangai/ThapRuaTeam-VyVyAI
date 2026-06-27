from __future__ import annotations

from app.services.model_router import ModelRole


class ProviderError(RuntimeError):
    """Sanitized provider error safe for logs and API warnings."""

    def __init__(
        self,
        message: str,
        *,
        provider_name: str,
        model_role: ModelRole | None = None,
        model_name: str | None = None,
        error_type: str | None = None,
    ) -> None:
        super().__init__(message)
        self.provider_name = provider_name
        self.model_role = model_role
        self.model_name = model_name
        self.error_type = error_type


class ProviderAuthenticationError(ProviderError):
    """Authentication, permission or API-key provider error."""


class ProviderModelAccessError(ProviderError):
    """Configured model is unavailable or unauthorized for the account."""


class ProviderInvocationError(ProviderError):
    """Generic provider invocation failure."""
