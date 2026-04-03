from pydantic import BaseModel
from typing import List
from models.testcase_model import TestCaseModel


class TestSuiteModel(BaseModel):
    name: str
    test_cases: List[TestCaseModel] = []
