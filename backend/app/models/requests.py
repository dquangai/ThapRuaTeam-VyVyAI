from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class Locale(StrEnum):
    VI = "vi"
    EN = "en"


class InvestigationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: Annotated[str, StringConstraints(min_length=10, max_length=12_000)]
    locale: Locale = Locale.VI
    use_web_search: bool = True
