from typing import List, Dict
from pathlib import Path

from models.testsuite_model import TestSuiteModel
from core.testcase_validator import TestCaseValidatorSummarizer


class MarkdownDocumentationGenerator:
    """
    Generates clean, human-readable Markdown documentation
    using summarized validation intent (NOT raw assertions).
    """

    def generate(
        self,
        suites: List[TestSuiteModel],
        project_summary: Dict,
        output_path: Path
    ) -> None:
        lines: List[str] = []
        summarizer = TestCaseValidatorSummarizer()

        # ============================
        # Title
        # ============================
        lines.append("# SoapUI Project Documentation\n")

        # ============================
        # Project Summary
        # ============================
        lines.append("## Project Summary\n")
        lines.append(f"- **Total Test Suites:** {project_summary['test_suites_count']}")
        lines.append(f"- **Total Test Cases:** {project_summary['test_cases_total']}")
        lines.append(f"- **Enabled Test Cases:** {project_summary['test_cases_enabled']}")
        lines.append(f"- **Disabled Test Cases:** {project_summary['test_cases_disabled']}\n")

        if project_summary["unique_endpoints"]:
            lines.append("### APIs Used")
            for ep in project_summary["unique_endpoints"]:
                lines.append(f"- `{ep}`")
            lines.append("")

        if project_summary["unique_operations"]:
            lines.append("### Operations Used")
            for op in project_summary["unique_operations"]:
                lines.append(f"- `{op}`")
            lines.append("")

        if project_summary["unique_queues"]:
            lines.append("### Queues Used")
            for q in project_summary["unique_queues"]:
                lines.append(f"- `{q}`")
            lines.append("")

        if project_summary["external_scripts"]:
            lines.append("### External Groovy Scripts")
            for s in project_summary["external_scripts"]:
                lines.append(f"- `{s}`")
            lines.append("")

        # ============================
        # Detailed Test Documentation
        # ============================
        lines.append("---\n")
        lines.append("## Test Suite Details\n")

        for suite in suites:
            lines.append(f"### Test Suite: {suite.name}\n")

            for tc in suite.test_cases:
                status = "Enabled" if tc.enabled else "Disabled"
                lines.append(f"#### Test Case: {tc.name} ({status})\n")

                # ✅ USE SUMMARIZER (THIS IS THE FIX)
                validations = summarizer.summarize(tc)

                if validations:
                    lines.append("**Validations:**")
                    for v in validations:
                        lines.append(f"- {v}")
                    lines.append("")

                if tc.external_scripts:
                    lines.append("**External Scripts:**")
                    for script in tc.external_scripts:
                        lines.append(f"- `{script}`")
                    lines.append("")

        # ============================
        # Write to file
        # ============================
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")
