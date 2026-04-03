from core.logger import setup_logger
from core.testcase_llm_input_builder import TestCaseLLMInputBuilder

logger = setup_logger("DocumentationGenerator")


class DocumentationGenerator:
    def __init__(self, llm_client):
        self.llm = llm_client

    def generate(self, enriched_project: dict) -> str:
        logger.info("Starting per-test-case documentation generation")

        docs = []
        test_suites = enriched_project.get("test_suites", [])

        # ---- Dynamic project summary (no assumptions) ----
        total_suites = len(test_suites)
        total_cases = sum(len(s.get("test_cases", [])) for s in test_suites)
        enabled_cases = sum(
            1
            for s in test_suites
            for tc in s.get("test_cases", [])
            if tc.get("enabled", True)
        )
        disabled_cases = total_cases - enabled_cases

        docs.append("# SoapUI Project Documentation\n")
        docs.append("## Project Summary\n")
        docs.append(f"- Total Test Suites: {total_suites}")
        docs.append(f"- Total Test Cases: {total_cases}")
        docs.append(f"- Enabled Test Cases: {enabled_cases}")
        docs.append(f"- Disabled Test Cases: {disabled_cases}\n")

        # ---- Per suite / per test case ----
        for suite in test_suites:
            suite_name = suite.get("name", "Unnamed Suite")
            docs.append(f"\n## Test Suite: {suite_name}\n")

            for tc in suite.get("test_cases", []):
                tc_name = tc.get("name", "Unnamed TestCase")
                logger.info(f"Generating docs for test case: {tc_name}")

                payload = TestCaseLLMInputBuilder.build(suite_name, tc)
                prompt = TestCaseLLMInputBuilder.to_prompt(payload)

                explanation = self.llm.chat([
                    {
                        "role": "system",
                        "content": "You are an expert SoapUI test analyst."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ])

                docs.append(f"### Test Case: {tc_name}")
                docs.append(explanation.strip())
                docs.append("\n---\n")

        logger.info("All test cases documented successfully")
        return "\n".join(docs)
