from typing import List, Optional
from lxml import etree

from models.assertion_model import AssertionModel


class AssertionExtractor:
    """
    Extracts REST + SOAP assertions from a SoapUI TestStep.
    Fully compatible with real-world SoapUI projects.
    """

    def __init__(self, teststep_element: etree._Element):
        self.teststep_element = teststep_element
        self.ns = teststep_element.nsmap

    def extract(self) -> List[AssertionModel]:
        assertions: List[AssertionModel] = []

        # Assertions may live directly under config OR deeper
        assertion_elements = self.teststep_element.xpath(
            ".//con:assertion",
            namespaces=self.ns
        )

        for assertion in assertion_elements:
            name = assertion.get("name", "UnnamedAssertion")
            assertion_type = assertion.get("type", "UNKNOWN")
            enabled_attr = assertion.get("enabled", "true")

            expected = self._extract_expected_value(assertion)
            operator = self._infer_operator(assertion_type)

            assertions.append(
                AssertionModel(
                    name=name,
                    type=assertion_type,
                    enabled=(enabled_attr.lower() != "false"),
                    expected=expected,
                    operator=operator
                )
            )

        return assertions

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------

    def _extract_expected_value(self, assertion: etree._Element) -> Optional[str]:
        """
        Extract expected/asserted value from different SoapUI assertion types.
        """

        # REST / generic
        expected = self._text(assertion, ".//con:expected")
        if expected:
            return expected

        path = self._text(assertion, ".//con:path")
        if path:
            return path

        # SOAP Simple Contains / Not Contains
        token = self._text(assertion, ".//token")
        if token:
            return token

        # SOAP Response (no explicit expected value)
        assertion_type = assertion.get("type", "")
        if assertion_type == "SOAP Response":
            return "SOAP response must be present"

        return None

    def _text(self, element: etree._Element, xpath: str) -> Optional[str]:
        el = element.find(xpath, namespaces=self.ns)
        if el is not None and el.text:
            return el.text.strip()
        return None

    def _infer_operator(self, assertion_type: str) -> str:
        """
        Converts SoapUI assertion types into semantic operators.
        """

        mapping = {
            # REST
            "JsonPath Match": "PRESENT",
            "XPath Match": "PRESENT",
            "Contains": "PRESENT",
            "Not Contains": "NOT_PRESENT",
            "Valid HTTP Status Codes": "EQUALS",

            # SOAP
            "SOAP Response": "RESPONSE_PRESENT",
            "Simple Contains": "PRESENT",
            "Simple Not Contains": "NOT_PRESENT",
        }

        return mapping.get(assertion_type, "UNKNOWN")
