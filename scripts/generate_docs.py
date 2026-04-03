"""
Layer 3: LLM-Enhanced Documentation Generator

Takes enriched semantic JSON from Layer 2 and generates
human-readable documentation using LLM reasoning.
"""

import json
from pathlib import Path

from core.logger import setup_logger
from core.llm_client import LLMClient
from core.testcase_llm_input_builder import TestCaseLLMInputBuilder
from core.prompt_loader import PromptLoader
from core.api_inventory_analyzer import APIInventoryAnalyzer, format_inventory_markdown


logger = setup_logger("DocumentationGenerator")


def main():
    """
    Generate LLM-enhanced documentation from enriched JSON.
    """
    # Configuration
    enriched_json_path = Path("output/layer2_enriched.json")
    output_path = Path("output/llm_documentation.md")

    if not enriched_json_path.exists():
        logger.error(f"Enriched JSON not found: {enriched_json_path}")
        logger.error("Please run 'python scripts/xml_to_json_runner.py' first")
        return

    logger.info("=" * 60)
    logger.info("LAYER 3: LLM-ENHANCED DOCUMENTATION GENERATION")
    logger.info("=" * 60)

    # Load enriched data
    logger.info(f"Loading enriched data from: {enriched_json_path}")
    with enriched_json_path.open("r", encoding="utf-8") as f:
        enriched_data = json.load(f)

    # Initialize LLM client
    # Configuration is loaded from .env file
    # See .env.example for all available options
    logger.info("Initializing LLM client from .env configuration")
    logger.info("(Configure provider, model, and API keys in .env file)")

    try:
        llm = LLMClient()
    except Exception as e:
        logger.error(f"Failed to initialize LLM client: {e}")
        logger.error("Please check your .env file configuration")
        return

    # Load system prompt
    try:
        system_prompt = PromptLoader.load("prompts/system.txt")
    except:
        system_prompt = "You are a senior QA automation architect who explains test projects clearly."

    # Generate documentation
    docs = []
    docs.append("# SoapUI Project Documentation")
    docs.append("*Generated using AI-powered analysis*\n")

    # Project summary
    project_info = enriched_data.get("project", {})
    docs.append("## Project Overview\n")
    docs.append(f"**Project Name:** {project_info.get('name', 'Unknown')}\n")

    test_suites = enriched_data.get("test_suites", [])
    total_cases = sum(len(suite.get("test_cases", [])) for suite in test_suites)
    enabled_cases = sum(
        1 for suite in test_suites
        for tc in suite.get("test_cases", [])
        if tc.get("enabled", True)
    )

    docs.append(f"- **Test Suites:** {len(test_suites)}")
    docs.append(f"- **Total Test Cases:** {total_cases}")
    docs.append(f"- **Enabled Test Cases:** {enabled_cases}")
    docs.append(f"- **Disabled Test Cases:** {total_cases - enabled_cases}\n")

    docs.append("---\n")

    # API Inventory Analysis
    logger.info("Analyzing API inventory (endpoints, operations, queues)...")
    inventory_analyzer = APIInventoryAnalyzer(enriched_data)
    inventory = inventory_analyzer.analyze()
    inventory_markdown = format_inventory_markdown(inventory)
    docs.append(inventory_markdown)

    # Per-suite documentation with LLM analysis
    docs.append("## Test Suite Details\n")
    docs.append("*Detailed analysis of each test case with AI-powered explanations*\n")

    for suite in test_suites:
        suite_name = suite.get("name", "Unnamed Suite")
        logger.info(f"\nProcessing Test Suite: {suite_name}")
        docs.append(f"### Test Suite: {suite_name}\n")

        for tc in suite.get("test_cases", []):
            tc_name = tc.get("name", "Unnamed TestCase")
            logger.info(f"  Analyzing Test Case: {tc_name}")

            status = "Enabled" if tc.get("enabled", True) else "Disabled"
            docs.append(f"#### Test Case: {tc_name} ({status})\n")

            # Build LLM input
            payload = TestCaseLLMInputBuilder.build(suite_name, tc)
            prompt = TestCaseLLMInputBuilder.to_prompt(payload)

            # Get LLM explanation
            try:
                explanation = llm.chat([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ])

                docs.append(explanation.strip())
                docs.append("\n---\n")

            except Exception as e:
                logger.error(f"LLM error for test case '{tc_name}': {e}")
                docs.append(f"*[Error generating explanation: {e}]*\n")
                docs.append("---\n")

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(docs), encoding="utf-8")

    logger.info("=" * 60)
    logger.info("DOCUMENTATION GENERATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Output: {output_path}")


if __name__ == "__main__":
    main()
