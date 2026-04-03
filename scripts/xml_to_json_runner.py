"""
Complete Three-Layer Pipeline Runner

Layer 1: XML → Raw JSON (lossless)
Layer 2: Raw JSON → Enriched Semantic JSON (deterministic)
Layer 3: Ready for LLM reasoning

This script executes Layers 1-2, preparing data for LLM processing.
"""

import os
from pathlib import Path
import json
from dotenv import load_dotenv

from core.xml_to_json import XMLToJSONConverter
from core.json_enricher import JSONStructureEnricher
from core.json_filter import JSONSemanticFilter
from core.logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger("ThreeLayerPipeline")


def main():
    """
    Execute the three-layer transformation pipeline.
    """
    # Configuration from .env
    input_file_path = os.getenv("INPUT_PROJECT_FILE", "input/small_soapui_project.xml")
    input_file = Path(input_file_path)

    # Validate input file exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please check INPUT_PROJECT_FILE in .env or place the file in the input/ directory")
        return

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Output paths
    raw_json_path = output_dir / "layer1_raw.json"
    enriched_json_path = output_dir / "layer2_enriched.json"
    filtered_json_path = output_dir / "layer2_filtered.json"

    logger.info("=" * 60)
    logger.info("STARTING THREE-LAYER PIPELINE")
    logger.info("=" * 60)
    logger.info(f"Input project: {input_file}")

    # ======================================
    # LAYER 1: XML → Raw JSON (Lossless)
    # ======================================
    logger.info("LAYER 1: Converting XML to raw JSON (lossless)...")

    converter = XMLToJSONConverter(input_file)
    raw_json = converter.convert()

    with raw_json_path.open("w", encoding="utf-8") as f:
        json.dump(raw_json, f, indent=2, ensure_ascii=False)

    logger.info(f"✓ Layer 1 complete: {raw_json_path}")

    # ======================================
    # LAYER 2: Raw JSON → Enriched Semantic JSON
    # ======================================
    logger.info("LAYER 2: Extracting semantic structure...")

    enricher = JSONStructureEnricher()
    enriched_json = enricher.enrich(raw_json)

    with enriched_json_path.open("w", encoding="utf-8") as f:
        json.dump(enriched_json, f, indent=2, ensure_ascii=False)

    logger.info(f"✓ Layer 2 enrichment complete: {enriched_json_path}")

    # ======================================
    # LAYER 2.5: Optional Semantic Filtering
    # ======================================
    logger.info("LAYER 2.5: Applying semantic filter (optional)...")

    semantic_filter = JSONSemanticFilter()
    filtered_json = semantic_filter.filter(raw_json)

    with filtered_json_path.open("w", encoding="utf-8") as f:
        json.dump(filtered_json, f, indent=2, ensure_ascii=False)

    logger.info(f"✓ Layer 2.5 filtering complete: {filtered_json_path}")

    # ======================================
    # Summary
    # ======================================
    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 60)

    # Print stats
    project_name = enriched_json.get("project", {}).get("name", "Unknown")
    test_suites = enriched_json.get("test_suites", [])
    total_cases = sum(len(suite.get("test_cases", [])) for suite in test_suites)

    logger.info(f"Project: {project_name}")
    logger.info(f"Test Suites: {len(test_suites)}")
    logger.info(f"Test Cases: {total_cases}")
    logger.info("")
    logger.info("Next step: Run 'python scripts/generate_docs.py' for LLM-enhanced documentation")


if __name__ == "__main__":
    main()
