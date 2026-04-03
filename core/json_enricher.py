"""
Layer 2: Semantic Structure Enricher

Converts raw lossless JSON into semantically enriched structure.

This is DETERMINISTIC extraction:
- No AI guessing
- No interpretation
- Project-agnostic SoapUI structure extraction
- Extracts: projects, test suites, test cases, test steps, assertions, endpoints
"""

from typing import Dict, Any, List, Optional


class JSONStructureEnricher:
    """
    Extracts SoapUI semantic structure from raw JSON tree.
    """

    def enrich(self, raw_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point: converts raw JSON tree into semantic structure.
        """
        root = raw_json.get("root")
        if not root:
            return {}

        project_info = self._extract_project_info(root)
        test_suites = self._extract_test_suites(root)

        return {
            "project": project_info,
            "test_suites": test_suites
        }

    def _extract_project_info(self, root: Dict[str, Any]) -> Dict[str, Any]:
        """Extract high-level project metadata."""
        attributes = root.get("attributes", {})

        return {
            "name": attributes.get("name", "Unnamed Project"),
            "type": "SoapUI Project"
        }

    def _extract_test_suites(self, root: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find all testSuite nodes in the tree."""
        test_suites = []

        # Find all testSuite nodes (recursive search)
        suite_nodes = self._find_nodes_by_tag(root, "testSuite")

        for suite_node in suite_nodes:
            suite_data = self._extract_test_suite(suite_node)
            if suite_data:
                test_suites.append(suite_data)

        return test_suites

    def _extract_test_suite(self, suite_node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract a single test suite with its test cases."""
        attributes = suite_node.get("attributes", {})

        suite_name = attributes.get("name", "Unnamed Suite")
        disabled = attributes.get("disabled", "false").lower() == "true"

        test_cases = []
        test_case_nodes = self._find_nodes_by_tag(suite_node, "testCase")

        for tc_node in test_case_nodes:
            tc_data = self._extract_test_case(tc_node)
            if tc_data:
                test_cases.append(tc_data)

        return {
            "name": suite_name,
            "enabled": not disabled,
            "test_cases": test_cases
        }

    def _extract_test_case(self, tc_node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract a single test case with its steps."""
        attributes = tc_node.get("attributes", {})

        tc_name = attributes.get("name", "Unnamed TestCase")
        disabled = attributes.get("disabled", "false").lower() == "true"

        test_steps = []
        step_nodes = self._find_nodes_by_tag(tc_node, "testStep")

        for step_node in step_nodes:
            step_data = self._extract_test_step(step_node)
            if step_data:
                test_steps.append(step_data)

        return {
            "name": tc_name,
            "enabled": not disabled,
            "test_steps": test_steps
        }

    def _extract_test_step(self, step_node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract a single test step with all relevant data."""
        attributes = step_node.get("attributes", {})

        step_name = attributes.get("name", "Unnamed Step")
        step_type = attributes.get("type", "unknown")
        disabled = attributes.get("disabled", "false").lower() == "true"

        step_data = {
            "name": step_name,
            "type": step_type,
            "enabled": not disabled
        }

        # Extract type-specific data
        if step_type in ("restrequest", "httprequest"):
            step_data["endpoint"] = self._find_text_by_tag(step_node, "endpoint")
            step_data["method"] = self._find_text_by_tag(step_node, "method")
            step_data["resource"] = self._find_text_by_tag(step_node, "resource")

        elif step_type == "request":  # SOAP
            step_data["endpoint"] = self._find_text_by_tag(step_node, "endpoint")
            step_data["operation"] = self._find_text_by_tag(step_node, "operation")

        elif step_type == "groovy":
            step_data["script"] = self._find_text_by_tag(step_node, "script")

        elif step_type == "properties":
            step_data["properties"] = self._extract_properties(step_node)

        elif step_type == "delay":
            delay_text = self._find_text_by_tag(step_node, "delay")
            if delay_text and delay_text.isdigit():
                step_data["delay_ms"] = int(delay_text)

        # Extract assertions (all step types can have them)
        assertions = self._extract_assertions(step_node)
        if assertions:
            step_data["assertions"] = assertions

        return step_data

    def _extract_assertions(self, parent_node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all assertion nodes from a parent."""
        assertions = []
        assertion_nodes = self._find_nodes_by_tag(parent_node, "assertion")

        for assertion_node in assertion_nodes:
            attributes = assertion_node.get("attributes", {})

            assertion_data = {
                "name": attributes.get("name", "Unnamed Assertion"),
                "type": attributes.get("type", "UNKNOWN")
            }

            # Extract expected value or path
            expected = self._find_text_by_tag(assertion_node, "expected")
            if expected:
                assertion_data["expected"] = expected

            path = self._find_text_by_tag(assertion_node, "path")
            if path:
                assertion_data["path"] = path

            assertions.append(assertion_data)

        return assertions

    def _extract_properties(self, parent_node: Dict[str, Any]) -> Dict[str, str]:
        """Extract property key-value pairs."""
        properties = {}
        prop_nodes = self._find_nodes_by_tag(parent_node, "property")

        for prop_node in prop_nodes:
            attributes = prop_node.get("attributes", {})
            name = attributes.get("name")
            value = attributes.get("value", "")

            if name:
                properties[name] = value

        return properties

    # ==========================================
    # Helper methods for tree traversal
    # ==========================================

    def _find_nodes_by_tag(self, node: Dict[str, Any], tag_suffix: str) -> List[Dict[str, Any]]:
        """
        Recursively find all nodes whose tag ends with the given suffix.
        Handles namespaced tags like 'namespace|testSuite'.
        """
        results = []

        node_tag = node.get("tag", "")
        if node_tag.endswith(tag_suffix):
            results.append(node)

        # Recurse into children
        for child in node.get("children", []):
            results.extend(self._find_nodes_by_tag(child, tag_suffix))

        return results

    def _find_text_by_tag(self, node: Dict[str, Any], tag_suffix: str) -> Optional[str]:
        """
        Find the first node with matching tag and return its text content.
        """
        nodes = self._find_nodes_by_tag(node, tag_suffix)
        if nodes and nodes[0].get("text"):
            return nodes[0]["text"].strip()
        return None
