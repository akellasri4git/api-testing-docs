from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class TestCaseModel:
    name: str
    enabled: bool

    # Intent buckets
    requests: List[Dict] = field(default_factory=list)
    validations: List[Dict] = field(default_factory=list)
    scripts: List[str] = field(default_factory=list)
    data_flows: List[str] = field(default_factory=list)

    external_scripts: List[str] = field(default_factory=list)
