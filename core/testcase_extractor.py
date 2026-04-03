from typing import List
from lxml import etree

from models.testsuite_model import TestSuiteModel
from models.testcase_model import TestCaseModel
from core.intent_detector import IntentDetector


class TestCaseExtractor:
    NS = {"con": "http://eviware.com/soapui/config"}

    def __init__(self, root: etree._Element):
        self.root = root

    def extract(self) -> List[TestSuiteModel]:
        suites = []

        for suite_elem in self.root.findall(".//con:testSuite", self.NS):
            suite = TestSuiteModel(
                name=suite_elem.attrib.get("name", "Unnamed TestSuite"),
                test_cases=[]
            )

            for tc_elem in suite_elem.findall(".//con:testCase", self.NS):
                enabled = tc_elem.attrib.get("disabled", "false") != "true"

                tc = TestCaseModel(
                    name=tc_elem.attrib.get("name", "Unnamed TestCase"),
                    enabled=enabled
                )

                for elem in tc_elem.iter():

                    # REQUESTS (🔥 NEW)
                    if IntentDetector.is_request(elem):
                        req = IntentDetector.extract_request(elem)
                        if req["endpoint"] or req["operation"]:
                            tc.requests.append(req)

                    # ASSERTIONS
                    if IntentDetector.is_assertion(elem):
                        tc.validations.append(
                            IntentDetector.extract_validation(elem)
                        )

                suite.test_cases.append(tc)

            suites.append(suite)

        return suites
