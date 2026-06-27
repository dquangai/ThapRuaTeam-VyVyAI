from __future__ import annotations

import inspect
from typing import Any, TypeVar

from pydantic import BaseModel

from app.core.config import MissingConfigurationError, Settings
from app.services.model_router import ModelRole, get_model_for_role
from app.services.provider_errors import (
    ProviderAuthenticationError,
    ProviderInvocationError,
    ProviderModelAccessError,
)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class OpenAIProvider:
    provider_name = "openai"

    def __init__(
        self,
        *,
        settings: Settings,
        model_role: ModelRole,
        client: Any | None = None,
    ) -> None:
        self.settings = settings
        self.model_role = model_role
        self._client = client

    async def structured(self, prompt: str, schema: type[SchemaT]) -> SchemaT | dict[str, Any]:
        model_name = get_model_for_role(self.model_role, self.settings)
        api_key = self.settings.openai_api_key
        if api_key is None:
            raise MissingConfigurationError(
                f"OPENAI_API_KEY is required for {self.model_role.value} model calls.",
                variable_name="OPENAI_API_KEY",
            )

        client = self._client or self._build_client(api_key.get_secret_value())
        try:
            response = await self._call_structured_client(
                client=client,
                prompt=prompt,
                schema=schema,
                model_name=model_name,
            )
            return _extract_structured_payload(response, schema)
        except MissingConfigurationError:
            raise
        except Exception as exc:
            raise _sanitized_provider_error(
                exc,
                provider_name=self.provider_name,
                model_role=self.model_role,
                model_name=model_name,
            ) from exc

    def _build_client(self, api_key: str) -> Any:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise ProviderInvocationError(
                "OpenAI SDK is not installed.",
                provider_name=self.provider_name,
                model_role=self.model_role,
                error_type="missing_sdk",
            ) from exc
        return AsyncOpenAI(api_key=api_key, timeout=self.settings.provider_timeout_float())

    async def _call_structured_client(
        self,
        *,
        client: Any,
        prompt: str,
        schema: type[SchemaT],
        model_name: str,
    ) -> Any:
        if hasattr(client, "structured"):
            result = client.structured(model=model_name, prompt=prompt, schema=schema)
            return await result if inspect.isawaitable(result) else result

        responses = getattr(client, "responses", None)
        parse = getattr(responses, "parse", None)
        if parse is not None:
            result = parse(
                model=model_name,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "Return only the requested structured data. "
                            "Do not include hidden reasoning."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                text_format=schema,
            )
            return await result if inspect.isawaitable(result) else result

        beta = getattr(client, "beta", None)
        chat = getattr(beta, "chat", None)
        completions = getattr(chat, "completions", None)
        chat_parse = getattr(completions, "parse", None)
        if chat_parse is not None:
            result = chat_parse(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Return only the requested structured data. "
                            "Do not include hidden reasoning."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format=schema,
            )
            return await result if inspect.isawaitable(result) else result

        raise ProviderInvocationError(
            "OpenAI client does not expose a supported structured-output method.",
            provider_name=self.provider_name,
            model_role=self.model_role,
            model_name=model_name,
            error_type="unsupported_client",
        )


def _extract_structured_payload[ModelT: BaseModel](
    response: Any,
    schema: type[ModelT],
) -> ModelT | dict[str, Any]:
    if isinstance(response, schema):
        return response
    if isinstance(response, dict):
        return response

    output_parsed = getattr(response, "output_parsed", None)
    if output_parsed is not None:
        return output_parsed

    choices = getattr(response, "choices", None)
    if choices:
        first_choice = choices[0]
        message = getattr(first_choice, "message", None)
        parsed = getattr(message, "parsed", None)
        if parsed is not None:
            return parsed

    if isinstance(response, BaseModel):
        return response.model_dump(mode="json")

    raise ValueError("Provider response did not contain structured output.")


def _sanitized_provider_error(
    exc: Exception,
    *,
    provider_name: str,
    model_role: ModelRole,
    model_name: str,
) -> ProviderInvocationError:
    error_type = exc.__class__.__name__
    message = (
        f"{provider_name} provider failed for role={model_role.value} "
        f"model={model_name}: {error_type}"
    )
    normalized = error_type.casefold()
    if "authentication" in normalized or "permission" in normalized or "apierror" in normalized:
        return ProviderAuthenticationError(
            message,
            provider_name=provider_name,
            model_role=model_role,
            model_name=model_name,
            error_type=error_type,
        )
    if "notfound" in normalized or "model" in normalized or "badrequest" in normalized:
        return ProviderModelAccessError(
            message,
            provider_name=provider_name,
            model_role=model_role,
            model_name=model_name,
            error_type=error_type,
        )
    return ProviderInvocationError(
        message,
        provider_name=provider_name,
        model_role=model_role,
        model_name=model_name,
        error_type=error_type,
    )
