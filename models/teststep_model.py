from pydantic import BaseModel
from typing import List, Optional, Dict
from models.assertion_model import AssertionModel


class TestStepModel(BaseModel):
    name: str
    step_type: str
    enabled: bool

    # Common technical metadata
    endpoint: Optional[str] = None
    operation: Optional[str] = None
    queue_name: Optional[str] = None

    # Script related
    script: Optional[str] = None
    external_scripts: List[str] = []

    # Properties
    properties: Dict[str, str] = {}

    # Property transfer
    transfers: List[str] = []

    # Delay
    delay_ms: Optional[int] = None

    # Data source
    datasource: Optional[str] = None

    assertions: List[AssertionModel] = []
