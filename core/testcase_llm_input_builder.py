"""
Layer 3: LLM Input Builder

Formats enriched test case data into LLM-friendly prompts.

This prepares the structured data from Layer 2 for LLM reasoning.
"""

import json
from typing import Dict, Any, List


class TestCaseLLMInputBuilder:
    """
    Converts enriched JSON test case data into a focused LLM prompt.
    """

    @staticmethod
    def build(test_suite_name: str, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant test case information for LLM consumption.
        """
        # Collect endpoints, operations from test steps
        endpoints = set()
        operations = []
        scripts = []

        for step in test_case.get("test_steps", []):
            if step.get("endpoint"):
                endpoints.add(step["endpoint"])

            if step.get("method") and step.get("resource"):
                operations.append(f"{step['method']} {step['resource']}")
            elif step.get("operation"):
                operations.append(step["operation"])

            if step.get("script"):
                scripts.append({
                    "step": step.get("name"),
                    "script_preview": step["script"][:200] + "..." if len(step["script"]) > 200 else step["script"]
                })

        # Collect all assertions from all steps
        all_assertions = []
        for step in test_case.get("test_steps", []):
            for assertion in step.get("assertions", []):
                all_assertions.append({
                    "step": step.get("name"),
                    "type": assertion.get("type"),
                    "name": assertion.get("name"),
                    "expected": assertion.get("expected"),
                    "path": assertion.get("path")
                })

        return {
            "test_suite": test_suite_name,
            "test_case": test_case["name"],
            "enabled": test_case.get("enabled", True),
            "endpoints": sorted(endpoints),
            "operations": operations,
            "test_steps": [
                {
                    "name": step.get("name"),
                    "type": step.get("type"),
                    "enabled": step.get("enabled", True)
                }
                for step in test_case.get("test_steps", [])
            ],
            "scripts": scripts,
            "assertions": all_assertions
        }

    @staticmethod
    def to_prompt(payload: Dict[str, Any]) -> str:
        """
        Format the payload as a clear LLM prompt.
        """
        prompt_parts = [
            "Analyze this SoapUI test case and explain what it does in plain English.",
            "",
            f"Test Suite: {payload['test_suite']}",
            f"Test Case: {payload['test_case']}",
            f"Status: {'Enabled' if payload['enabled'] else 'Disabled'}",
            ""
        ]

        if payload['endpoints']:
            prompt_parts.append("Endpoints:")
            for ep in payload['endpoints']:
                prompt_parts.append(f"  - {ep}")
            prompt_parts.append("")

        if payload['operations']:
            prompt_parts.append("Operations:")
            for op in payload['operations']:
                prompt_parts.append(f"  - {op}")
            prompt_parts.append("")

        if payload['test_steps']:
            prompt_parts.append("Test Steps:")
            for i, step in enumerate(payload['test_steps'], 1):
                status = "" if step['enabled'] else " (disabled)"
                prompt_parts.append(f"  {i}. {step['name']} [{step['type']}]{status}")
            prompt_parts.append("")

        if payload['assertions']:
            prompt_parts.append("Validations/Assertions:")
            for assertion in payload['assertions']:
                parts = [f"  - {assertion['name']} ({assertion['type']})"]
                if assertion.get('expected'):
                    parts.append(f" expects: {assertion['expected']}")
                if assertion.get('path'):
                    parts.append(f" at path: {assertion['path']}")
                prompt_parts.append("".join(parts))
            prompt_parts.append("")

        if payload['scripts']:
            prompt_parts.append("Scripts Used:")
            for script in payload['scripts']:
                prompt_parts.append(f"  - In step '{script['step']}':")
                prompt_parts.append(f"    {script['script_preview']}")
            prompt_parts.append("")

        prompt_parts.extend([
            "Please explain:",
            "1. What this test case does (purpose and flow)",
            "2. What it validates and why",
            "3. Any potential issues or duplications with other tests (if obvious)"
        ])

        return "\n".join(prompt_parts)
