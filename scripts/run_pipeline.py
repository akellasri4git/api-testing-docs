"""
Unified Pipeline Runner
Runs the complete three-layer pipeline with LLM documentation generation in one command

Usage:
    python -m scripts.run_pipeline              # Generates Markdown
    python -m scripts.run_pipeline --docx       # Generates DOCX
    python -m scripts.run_pipeline --both       # Generates both Markdown and DOCX
"""

import argparse
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import os

from core.xml_to_json import XMLToJSONConverter
from core.postman_to_json import PostmanToJSONConverter, detect_format
from core.json_enricher import JSONStructureEnricher
from core.json_filter import JSONSemanticFilter
from core.llm_client import LLMClient
from core.logger import setup_logger
from core.testcase_llm_input_builder import TestCaseLLMInputBuilder
from core.prompt_loader import PromptLoader
from core.api_inventory_analyzer import APIInventoryAnalyzer, format_inventory_markdown

# Import md_to_docx converter
from scripts.md_to_docx import MarkdownToDocxConverter

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger("UnifiedPipeline")


def run_layer1(input_file: str, output_file: str):
    """Layer 1: Auto-detect format and convert to normalized JSON"""
    logger.info("=" * 60)
    logger.info("LAYER 1: Auto-detecting format and converting...")
    logger.info("=" * 60)

    # Auto-detect format
    file_format = detect_format(input_file)
    logger.info(f"📋 Detected format: {file_format.upper()}")

    # Use appropriate converter
    if file_format == 'postman':
        logger.info("Converting Postman collection to normalized JSON...")
        converter = PostmanToJSONConverter(input_file)
        raw_json = converter.convert()
    elif file_format == 'soapui':
        logger.info("Converting SoapUI XML to raw JSON (lossless)...")
        converter = XMLToJSONConverter(input_file)
        raw_json = converter.convert()
    else:
        raise ValueError(f"Unsupported format. Please provide SoapUI XML or Postman JSON collection.")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(raw_json, f, indent=2, ensure_ascii=False)

    logger.info(f"✓ Layer 1 complete: {output_file}")
    return raw_json


def run_layer2(raw_json: dict, enriched_output: str, filtered_output: str):
    """Layer 2: Semantic enrichment and filtering"""
    logger.info("=" * 60)
    logger.info("LAYER 2: Extracting semantic structure...")
    logger.info("=" * 60)

    # Check if already enriched (Postman format comes pre-normalized)
    if "test_suites" in raw_json and "project" in raw_json:
        logger.info("✓ Input already in normalized format (Postman), skipping enrichment...")
        enriched_json = raw_json
    else:
        # Enrichment for SoapUI XML
        enricher = JSONStructureEnricher()
        enriched_json = enricher.enrich(raw_json)

    with open(enriched_output, 'w', encoding='utf-8') as f:
        json.dump(enriched_json, f, indent=2, ensure_ascii=False)
    logger.info(f"✓ Layer 2 enrichment complete: {enriched_output}")

    # Filtering (applies to raw_json only for SoapUI, skip for Postman)
    if "test_suites" not in raw_json:
        logger.info("LAYER 2.5: Applying semantic filter (optional)...")
        semantic_filter = JSONSemanticFilter()
        filtered_json = semantic_filter.filter(raw_json)

        with open(filtered_output, 'w', encoding='utf-8') as f:
            json.dump(filtered_json, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Layer 2.5 filtering complete: {filtered_output}")
    else:
        logger.info("✓ Skipping filtering for Postman format")

    return enriched_json


def run_layer3_markdown(enriched_json: dict, output_file: str):
    """Layer 3: LLM documentation generation (Markdown)"""
    logger.info("=" * 60)
    logger.info("LAYER 3: Generating LLM-enhanced Markdown documentation...")
    logger.info("=" * 60)

    # Initialize LLM client
    llm = LLMClient()

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
    project_info = enriched_json.get("project", {})
    docs.append("## Project Overview\n")
    docs.append(f"**Project Name:** {project_info.get('name', 'Unknown')}\n")

    test_suites = enriched_json.get("test_suites", [])
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
    inventory_analyzer = APIInventoryAnalyzer(enriched_json)
    inventory = inventory_analyzer.analyze()
    inventory_markdown = format_inventory_markdown(inventory)
    docs.append(inventory_markdown)

    # Per-suite documentation with LLM analysis
    docs.append("## Test Suite Details\n")
    docs.append("*Detailed analysis of each test case with AI-powered explanations*\n")

    for suite in test_suites:
        suite_name = suite.get("name", "Unnamed Suite")
        logger.info(f"Processing Test Suite: {suite_name}")
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
    markdown_content = "\n".join(docs)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    logger.info(f"✓ Markdown documentation generated: {output_file}")


def run_layer3_docx(enriched_json: dict, output_file: str):
    """Layer 3: LLM documentation generation (DOCX)"""
    logger.info("=" * 60)
    logger.info("LAYER 3: Generating LLM-enhanced DOCX documentation...")
    logger.info("=" * 60)

    # Import here to avoid requiring docx if not needed
    from scripts.generate_docx_docs import DocxDocumentationGenerator

    # Initialize LLM client
    llm_client = LLMClient()

    # Generate DOCX
    generator = DocxDocumentationGenerator(enriched_json, llm_client)
    doc = generator.generate()
    generator.save(output_file)

    logger.info(f"✓ DOCX documentation generated: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Run the complete SoapUI documentation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m scripts.run_pipeline              # Generate Markdown + DOCX (both formats)
  python -m scripts.run_pipeline --skip-json  # Skip Layer 1-2, regenerate docs only

Note: The pipeline now AUTOMATICALLY generates BOTH Markdown and DOCX.
The DOCX is created by converting Markdown (fast, <1 second).
        """
    )

    # Remove --docx and --both flags since we always generate both now
    parser.add_argument(
        '--skip-json',
        action='store_true',
        help='Skip Layer 1-2 if JSON files already exist (faster for re-runs)'
    )

    # Keep these for backward compatibility but mark as deprecated
    parser.add_argument(
        '--docx',
        action='store_true',
        help='(Deprecated: DOCX is now generated automatically)'
    )


    parser.add_argument(
        '--skip-json',
        action='store_true',
        help='Skip Layer 1-2 if JSON files already exist (faster for re-runs)'
    )

    args = parser.parse_args()

    # Configuration
    input_project = os.getenv('INPUT_PROJECT_FILE', 'input/small_soapui_project.xml')
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)

    layer1_output = output_dir / 'layer1_raw.json'
    layer2_enriched = output_dir / 'layer2_enriched.json'
    layer2_filtered = output_dir / 'layer2_filtered.json'
    markdown_output = output_dir / 'llm_documentation.md'
    docx_output = output_dir / 'Understanding_Document.docx'

    logger.info("=" * 60)
    logger.info("UNIFIED PIPELINE - THREE-LAYER ARCHITECTURE")
    logger.info("=" * 60)
    logger.info(f"Input: {input_project}")
    logger.info("")

    try:
        # Layer 1-2: XML → JSON (can be skipped if files exist)
        if args.skip_json and layer2_enriched.exists():
            logger.info("⏭️  Skipping Layer 1-2 (using existing JSON)")
            with open(layer2_enriched, 'r', encoding='utf-8') as f:
                enriched_json = json.load(f)
        else:
            # Layer 1
            raw_json = run_layer1(input_project, str(layer1_output))

            # Layer 2
            enriched_json = run_layer2(raw_json, str(layer2_enriched), str(layer2_filtered))

        logger.info("")

        # Layer 3: Generate Markdown documentation
        run_layer3_markdown(enriched_json, str(markdown_output))
        logger.info("")

        # Automatically convert Markdown to DOCX (fast!)
        logger.info("=" * 60)
        logger.info("Converting Markdown to DOCX...")
        logger.info("=" * 60)
        try:
            converter = MarkdownToDocxConverter(str(markdown_output))
            converter.convert(str(docx_output))
            logger.info(f"✓ DOCX generated: {docx_output}")
        except Exception as e:
            logger.error(f"Failed to generate DOCX: {e}")
            logger.error("Markdown documentation is still available")

        # Summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ PIPELINE COMPLETE!")
        logger.info("=" * 60)
        logger.info("Generated files:")
        if not args.skip_json:
            logger.info(f"  • {layer1_output}")
            logger.info(f"  • {layer2_enriched}")
            logger.info(f"  • {layer2_filtered}")
        logger.info(f"  • {markdown_output}")
        logger.info(f"  • {docx_output} ⭐ (auto-converted from Markdown)")
        logger.info("")
        logger.info("📄 Your documentation is ready!")
        logger.info(f"   Markdown: {markdown_output}")
        logger.info(f"   Word Doc: {docx_output}")
        logger.info("")

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()
