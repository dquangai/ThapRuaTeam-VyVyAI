from __future__ import annotations

from enum import StrEnum

from app.core.config import MissingConfigurationError, Settings, UnknownModelRoleError


class ModelRole(StrEnum):
    FAST = "fast"
    EXPERT = "expert"
    JUDGE = "judge"
    REPORT = "report"


_MODEL_FIELD_BY_ROLE = {
    ModelRole.FAST: "openai_model_fast",
    ModelRole.EXPERT: "openai_model_expert",
    ModelRole.JUDGE: "openai_model_judge",
    ModelRole.REPORT: "openai_model_report",
}

_MODEL_ENV_BY_ROLE = {
    ModelRole.FAST: "OPENAI_MODEL_FAST",
    ModelRole.EXPERT: "OPENAI_MODEL_EXPERT",
    ModelRole.JUDGE: "OPENAI_MODEL_JUDGE",
    ModelRole.REPORT: "OPENAI_MODEL_REPORT",
}


def get_model_for_role(role: ModelRole | str, settings: Settings) -> str:
    resolved_role = _coerce_role(role)
    field_name = _MODEL_FIELD_BY_ROLE[resolved_role]
    model_name = getattr(settings, field_name)
    if not model_name:
        variable_name = _MODEL_ENV_BY_ROLE[resolved_role]
        raise MissingConfigurationError(
            f"{variable_name} is required for {resolved_role.value} model calls.",
            variable_name=variable_name,
        )
    return model_name


def model_env_var_for_role(role: ModelRole | str) -> str:
    return _MODEL_ENV_BY_ROLE[_coerce_role(role)]


def _coerce_role(role: ModelRole | str) -> ModelRole:
    if isinstance(role, ModelRole):
        return role
    try:
        return ModelRole(role)
    except ValueError as exc:
        raise UnknownModelRoleError(
            f"Unknown model role: {role}",
            variable_name="MODEL_ROLE",
        ) from exc
