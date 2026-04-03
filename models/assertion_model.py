from pydantic import BaseModel
from typing import Optional


class AssertionModel(BaseModel):
    name: str
    type: str
    enabled: bool
    expected: Optional[str] = None
    operator: Optional[str] = None
