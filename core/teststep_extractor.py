from typing import List
from xml.parsers.expat import model
from core import assertion_extractor
from lxml import etree

from models.teststep_model import TestStepModel
from core.assertion_extractor import AssertionExtractor



class TestStepExtractor:
    """
    Extracts ALL common SoapUI TestStep types in a safe, extensible way.
    """

    def __init__(self, testcase_element: etree._Element):
        self.testcase_element = testcase_element

    def extract(self) -> List[TestStepModel]:
        steps: List[TestStepModel] = []

        step_elements = self.testcase_element.xpath(
            ".//con:testStep",
            namespaces=self.testcase_element.nsmap
        )

        for step in step_elements:
            step_type = step.get("type", "unknown")
            disabled_attr = step.get("disabled", "false")

            model = TestStepModel(
                name=step.get("name", "UnnamedTestStep"),
                step_type=step_type,
                enabled=(disabled_attr.lower() != "true")
            )

            # =========================
            # REST / HTTP Request
            # =========================
            if step_type in ("restrequest", "httprequest"):
                model.endpoint = self._text(step, ".//con:endpoint")
                resource = self._text(step, ".//con:resource")
                method = self._text(step, ".//con:method")

                if resource and method:
                    model.operation = f"{method} {resource}"

            # =========================
            # SOAP Request
            # =========================
            elif step_type == "request":
                model.operation = self._text(step, ".//con:operation")

            # =========================
            # JMS
            # =========================
            elif step_type == "jms":
                model.queue_name = self._text(step, ".//con:queueName")

            # =========================
            # Groovy Script
            # =========================
            elif step_type == "groovy":
                script_text = self._text(step, ".//con:script")
                model.script = script_text

                if script_text:
                    model.external_scripts = self._extract_external_scripts(script_text)

            # =========================
            # Properties Step
            # =========================
            elif step_type == "properties":
                for prop in step.xpath(".//con:property", namespaces=step.nsmap):
                    name = prop.get("name")
                    value = prop.get("value")
                    if name:
                        model.properties[name] = value

            # =========================
            # Property Transfer
            # =========================
            elif step_type == "propertytransfer":
                for transfer in step.xpath(".//con:transfer", namespaces=step.nsmap):
                    src = transfer.get("source")
                    tgt = transfer.get("target")
                    model.transfers.append(f"{src} -> {tgt}")

            # =========================
            # Delay
            # =========================
            elif step_type == "delay":
                delay = self._text(step, ".//con:delay")
                if delay and delay.isdigit():
                    model.delay_ms = int(delay)

            # =========================
            # DataSource
            # =========================
            elif step_type == "datasource":
                model.datasource = self._text(step, ".//con:query")

            # =========================
            # Unknown / Custom Step
            # =========================
            else:
                # Keep step_type only — future-proof
                pass
                # Extract assertions inside this test step
            assertion_extractor = AssertionExtractor(step)
            model.assertions = assertion_extractor.extract()

            steps.append(model)

        return steps

    # ---------------------------
    # Helpers
    # ---------------------------
    def _text(self, element: etree._Element, xpath: str) -> str | None:
        el = element.find(xpath, namespaces=element.nsmap)
        return el.text.strip() if el is not None and el.text else None

    def _extract_external_scripts(self, script: str) -> List[str]:
        """
        Extracts external groovy script references.
        Example: loadScript("path/file.groovy")
        """
        results = []
        for line in script.splitlines():
            if "loadScript" in line and '"' in line:
                try:
                    results.append(line.split('"')[1])
                except IndexError:
                    pass
        return results
