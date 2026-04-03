from pydantic import BaseModel
from typing import List
from models.testsuite_model import TestSuiteModel


class SoapUIProjectModel(BaseModel):
    name: str
    test_suites: List[TestSuiteModel] = []
