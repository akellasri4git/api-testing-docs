"""
Direct XML Parser (No LLM)

This is the simpler, faster alternative to the LLM pipeline.
Uses XPath-based extraction for quick documentation generation.

When to use this:
- You don't have Ollama installed
- You need fast results without AI analysis
- You want basic structural documentation

For AI-powered explanations, use:
1. python scripts/xml_to_json_runner.py
2. python scripts/generate_docs.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from core.project_loader import SoapUIProjectLoader
from core.testcase_extractor import TestCaseExtractor
from core.testcase_validator import TestCaseValidatorSummarizer
from core.script_reference_resolver import ScriptReferenceResolver
from core.project_aggregator import ProjectAggregator
from documentation.markdown_generator import MarkdownDocumentationGenerator
from core.logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger("DirectParser")


def main():
    """
    Direct XML parsing without LLM - fast and simple.
    """
    logger.info("=" * 60)
    logger.info("DIRECT XML PARSER (NO LLM)")
    logger.info("=" * 60)

    # Configuration from .env
    input_file_path = os.getenv("INPUT_PROJECT_FILE", "input/small_soapui_project.xml")
    input_file = Path(input_file_path)
    output_file = Path("output/documentation.md")

    # Validate input file exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please check INPUT_PROJECT_FILE in .env or place the file in the input/ directory")
        return

    # Load SoapUI project
    logger.info(f"Loading SoapUI project: {input_file}")
    loader = SoapUIProjectLoader(str(input_file))
    root = loader.load()

    # Extract test suites & test cases
    logger.info("Extracting test suites and test cases...")
    suites = TestCaseExtractor(root).extract()

    # Initialize helpers
    summarizer = TestCaseValidatorSummarizer()
    resolver = ScriptReferenceResolver(scripts_root=Path("input"))
    aggregator = ProjectAggregator()

    # Print test case details to console
    for suite in suites:
        print(f"\n{'=' * 50}")
        print(f"TestSuite: {suite.name}")
        print(f"{'=' * 50}")

        for tc in suite.test_cases:
            print(f"\n  TestCase: {tc.name}")
            print(f"  Enabled: {tc.enabled}")

            # Validations
            validations = summarizer.summarize(tc)
            if validations:
                print("  Validations:")
                for v in validations:
                    print(f"    - {v}")

            # External scripts
            if tc.external_scripts:
                print("  External Scripts:")
                intents = resolver.resolve(tc.external_scripts)
                for script, intent in intents.items():
                    print(f"    - {script} → {intent}")

    # Generate project-level summary
    logger.info("Aggregating project summary...")
    project_summary = aggregator.aggregate(suites)

    print(f"\n{'=' * 50}")
    print("PROJECT SUMMARY")
    print(f"{'=' * 50}")

    for key, value in project_summary.items():
        print(f"{key}: {value}")

    # Generate Markdown documentation
    logger.info("Generating Markdown documentation...")
    doc_generator = MarkdownDocumentationGenerator()
    doc_generator.generate(
        suites=suites,
        project_summary=project_summary,
        output_path=output_file
    )

    logger.info("=" * 60)
    logger.info(f"Documentation generated: {output_file}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
