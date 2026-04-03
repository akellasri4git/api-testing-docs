# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **AI-powered API Testing Project Explainer**, not a traditional parser or rule engine.

**The Core Problem**: API testing projects (SoapUI XML, Postman JSON) are huge, inconsistent across teams, hard to understand for new people, and poorly documented. This tool answers: *"I've never seen this testing project before — tell me what it does."*

**Input:**
- SoapUI XML projects (any structure, any version)
- Postman JSON collections (v2.0+)

**Output**: Human-readable DOCX documentation explaining WHAT the tests do, HOW they work, and WHAT they validate

This is a **structure-aware + LLM-reasoning system** that converts unreadable testing configs into explainable system behavior without assuming how the project is built.

## Supported Formats

| Format | Tool | Auto-Detection | Parser Module |
|--------|------|----------------|---------------|
| XML | SoapUI | ✅ Yes | `core/xml_to_json.py` |
| JSON | Postman | ✅ Yes | `core/postman_to_json.py` |

The system automatically detects format based on file extension and content structure.

## Running the Project

### Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure project
cp .env.example .env
# Edit .env to set INPUT_PROJECT_FILE and LLM provider settings
```

### Main Execution Paths

**Path 1: Direct parsing without LLM (simpler, faster)**
```bash
python -m scripts.run_parser
```
Outputs to: `output/documentation.md`

**Path 2: XML → JSON → LLM-enriched documentation (RECOMMENDED)**
```bash
# UNIFIED PIPELINE (SIMPLEST - AUTO-GENERATES BOTH MD + DOCX!)
python -m scripts.run_pipeline              # Generates Markdown + DOCX (~30 min)

# Fast re-run (skip XML/JSON parsing)
python -m scripts.run_pipeline --skip-json  # Only regenerates docs (~30 min)

# Manual conversion (if needed)
python -m scripts.md_to_docx                 # Convert existing MD to DOCX (<1 sec)

# Step-by-step (for debugging)
python -m scripts.xml_to_json_runner        # Layers 1-2 only
python -m scripts.generate_docs              # Layer 3 (Markdown only)
python -m scripts.md_to_docx                 # Convert to DOCX
```
Outputs:
- `output/layer1_raw.json` - Lossless XML→JSON conversion
- `output/layer2_enriched.json` - Semantic structure extraction
- `output/llm_documentation.md` - AI-enhanced Markdown documentation
- `output/Understanding_Document.docx` - Professional DOCX ⭐ (auto-generated)

**Path 3: Web UI (no command line needed)**
```bash
python app.py
# Open browser to http://localhost:5000
```
- Upload SoapUI XML through web interface
- Select LLM provider from dropdown
- Get DOCX documentation with real-time progress updates
- **Updated**: Now uses fast MD→DOCX conversion (same as CLI pipeline)

### Configuration

**Primary configuration**: `.env` file (copy from `.env.example`)
- `INPUT_PROJECT_FILE`: Path to SoapUI XML project
- `LLM_PROVIDER`: Choose from `ollama`, `openai`, `anthropic`, `groq`, `azure`
- Provider-specific settings (API keys, models, endpoints)
- Generation parameters (temperature, max tokens, timeout)

**Legacy YAML configs** (still supported):
- `config/app_config.yaml`: Input/output paths, analysis settings
- `config/llm_config.yaml`: LLM temperature, max tokens, prompt paths
- `config/logging_config.yaml`: Logging configuration

**LLM Provider Setup**:
- **Ollama (local, free)**: Install from https://ollama.com, then `ollama pull mistral:latest`
- **OpenAI/Anthropic/Groq (cloud)**: Set API key in `.env`, no local installation needed

## Architecture

This system uses a **three-layer architecture** that separates deterministic extraction from AI reasoning:

```
Layer 1: Lossless Preservation  →  Layer 2: Semantic Enrichment  →  Layer 3: LLM Reasoning
(No interpretation)                 (Deterministic extraction)        (Per-test explanations)
```

### Layer 1: SoapUI XML → Raw Structural JSON (Lossless)

**What happens**: Convert entire SoapUI XML into tree-shaped JSON, preserving:
- All tags, attributes, values, hierarchy
- Namespaces (using `namespace|tag` format)
- Order and structure

**Key principle**: "We don't understand yet — we just preserve."

**Implementation**: `XMLToJSONConverter` (core/xml_to_json.py)
- Lossless conversion, no SoapUI-specific logic
- XML is hard for LLMs; JSON is LLM-friendly
- No data is lost, no assumptions about structure

### Layer 2: Raw JSON → Enriched Semantic JSON (Still Deterministic)

**What happens**: Extract structure deterministically from the raw tree:
- Project name, interfaces (REST/SOAP/JMS), endpoints
- TestSuites, TestCases, TestSteps
- Step types (restrequest, groovy, properties, delay, request)
- Assertions, scripts (inline + external references)
- Enabled/disabled flags

**Output**: Clean, normalized JSON structure like:
```json
{
  "project": {...},
  "test_suites": [
    {
      "name": "...",
      "test_cases": [
        {
          "name": "...",
          "steps": [...],
          "assertions": [...]
        }
      ]
    }
  ]
}
```

**Why this layer is critical**:
- Still no AI guessing
- Still project-agnostic and future-proof
- Provides complete context for LLM

**Implementation**: `JSONStructureEnricher` (core/json_enricher.py) and `JSONSemanticFilter` (core/json_filter.py)

### Layer 3: Per-Test-Case LLM Reasoning (The Magic)

**What the LLM receives** (for each test case):
- Test case name, step sequence
- Endpoints used, assertions, scripts
- Parameters and properties

**What the LLM does** (reasoning, not guessing):
- What is the purpose of this test?
- What business/API behavior is validated?
- What is expected vs forbidden?
- Is this test duplicated?
- Is it smoke/regression/negative/validation?
- What would a human say this test does?

**Output**: Human-quality explanation like:
> "This test sends a GET request to the Directions API using origin/destination parameters. It validates that the response structure is valid XML and contains route information. This test is functionally similar to 'Simple Tests' in the Distance Matrix suite."

**Implementation**: `DocumentationGenerator` (core/documentation_generator.py) with `LLMClient`

### Two Execution Paths

**Path 1: Direct extraction (no LLM)** - `scripts/run_parser.py`
1. `SoapUIProjectLoader` - Validates and loads XML
2. `TestCaseExtractor` - Extracts test suites/cases using namespace-aware XPath
3. `TestCaseValidatorSummarizer` - Summarizes assertions
4. `ScriptReferenceResolver` - Resolves external Groovy scripts
5. `ProjectAggregator` - Builds project-level summary
6. `MarkdownDocumentationGenerator` - Outputs structured Markdown

**Path 2: LLM-enhanced** - `scripts/xml_to_json_runner.py` → `scripts/generate_docs.py` or `scripts/generate_docx_docs.py`
1. Layer 1: `XMLToJSONConverter` - Lossless conversion
2. Layer 2: `JSONStructureEnricher` + `JSONSemanticFilter` - Semantic enrichment
3. Layer 3: `LLMClient` + `DocumentationGenerator` - AI-powered explanations

**Path 3: Web UI** - `app.py` (Flask application)
- Provides web interface for non-technical users
- Handles file uploads, background processing, real-time progress updates
- Uses same three-layer architecture internally
- Outputs DOCX format only

## Core Design Principles

### Separation of Concerns

**Deterministic (Layers 1-2)**:
- Structure preservation
- Semantic extraction
- Counting, classification, hierarchy mapping

**Probabilistic (Layer 3)**:
- Natural language explanation
- Intent summarization
- Deduplication detection
- Business context reasoning

### What the LLM Does vs Doesn't Do

**LLM is used FOR**:
- Explanation (what does this test do?)
- Summarization (plain English descriptions)
- Deduplication detection (are these tests similar?)
- Natural language clarity

**LLM is NOT used FOR**:
- Parsing XML/JSON
- Counting test cases
- Structural discovery
- Extracting assertions or endpoints

### Why This Design is Correct and Scalable

**We are NOT**:
- Hardcoding SoapUI schemas
- Relying on fragile XPath expressions
- Guessing without data
- Coupling to SoapUI versions
- Embedding business logic

**We ARE**:
- Preserving complete structure
- Using semantic enrichment
- Isolating AI to per-test reasoning (safe + scalable)
- Keeping deterministic and probabilistic work separate

### Key Modules

**models/** - Pydantic data models
- `project_model.py`: Overall project structure
- `testsuite_model.py`: Test suite container
- `testcase_model.py`: Single test case with requests, validations, scripts
- `teststep_model.py`: Individual test step representation
- `assertion_model.py`: Test assertion data model

**core/** - Business logic
- `project_loader.py`: XML validation and loading
- `testcase_extractor.py`: Extracts test suites/cases using namespace-aware XPath
- `teststep_extractor.py`: Extracts individual test steps
- `assertion_extractor.py`: Extracts and parses assertions
- `intent_detector.py`: Identifies requests, assertions, operations from XML elements
- `xml_to_json.py`: Layer 1 - Lossless XML → JSON converter for SoapUI (preserves all attributes, namespaces, order)
- `postman_to_json.py`: Layer 1 - Postman collection → Normalized JSON converter (auto-detects format, parses requests/tests)
- `json_enricher.py`: Layer 2 - Semantic structure enrichment for SoapUI (extracts test suites, cases, steps)
- `json_filter.py`: Layer 2 - Semantic filtering and cleanup for SoapUI
- `llm_client.py`: Multi-provider LLM integration (Ollama, OpenAI, Anthropic, Groq, Azure)
- `documentation_generator.py`: Layer 3 - LLM-based per-test-case documentation (Markdown output)
- `testcase_llm_input_builder.py`: Builds LLM-ready prompts from test case data
- `testcase_validator.py`: Summarizes assertions into human-readable validation intent
- `script_reference_resolver.py`: Resolves external Groovy script references
- `project_aggregator.py`: Aggregates project-level statistics and summaries
- `prompt_loader.py`: Loads LLM prompt templates
- `api_inventory_analyzer.py`: Analyzes and categorizes API endpoints
- `logger.py`: Centralized logging configuration

**documentation/** - Output formatters
- `markdown_generator.py`: Clean Markdown without LLM (uses validation summaries)

**scripts/** - Entry points
- `run_parser.py`: Path 1 - Direct XPath-based parsing (no LLM)
- `run_pipeline.py`: Unified pipeline - runs all layers with single command
- `xml_to_json_runner.py`: Path 2 Step 1 - XML → JSON conversion (Layers 1-2)
- `generate_docs.py`: Path 2 Step 2 - LLM-enhanced Markdown documentation generation
- `generate_docx_docs.py`: LLM-enhanced Word document generation (slow, not recommended)
- `md_to_docx.py`: Convert existing Markdown to professional DOCX (<1 sec - RECOMMENDED)
- `test_llm.py`: Test LLM connectivity and configuration (IMPORTANT: run this first to verify LLM setup)

**prompts/** - LLM prompt templates
- `system.txt`: System persona (senior QA architect)
- `documentation.txt`: Documentation format instructions

**utils/** - Utility functions
- `file_utils.py`: File I/O operations
- `xml_utils.py`: XML parsing helpers
- `groovy_utils.py`: Groovy script analysis
- `string_utils.py`: String manipulation utilities

### Important Implementation Details

1. **Namespace-aware XML parsing**: All SoapUI elements use the `con:` namespace (`http://eviware.com/soapui/config`). XPath queries MUST use this namespace prefix or they will fail. Always register the namespace: `namespaces = {'con': 'http://eviware.com/soapui/config'}`.

2. **Intent detection**: The `IntentDetector` classifies XML elements into semantic buckets:
   - Requests (endpoints, operations)
   - Assertions/validations
   - Scripts (inline Groovy)
   - Data flows

3. **Validation summarization**: `TestCaseValidatorSummarizer` converts technical assertions (XPath, JSONPath, status codes) into human-readable intent without using LLM.

4. **External script resolution**: The `ScriptReferenceResolver` loads external Groovy scripts from `input/external_scripts/` and uses simple keyword matching to infer intent. Max depth: 3 levels (configurable).

5. **Per-test-case isolation**: LLM reasoning happens independently for each test case, preventing cross-contamination and enabling parallel processing. Each test case gets its own LLM call with complete context.

6. **Module imports**: All scripts use `python -m` syntax (e.g., `python -m scripts.run_parser`) to ensure proper module resolution from project root.

### Critical Design Constraints

**DO NOT**:
- Use LLM for structural extraction (counting, parsing, discovery)
- Hardcode SoapUI version-specific schemas
- Make assumptions about project structure in Layer 1
- Mix deterministic and probabilistic logic in the same module
- Add interpretation logic to `xml_to_json.py` (lossless only)

**ALWAYS**:
- Preserve layer separation (1: preserve, 2: extract, 3: explain)
- Use namespace-aware XPath for all SoapUI XML queries
- Validate XML structure before parsing
- Handle missing/malformed XML elements gracefully
- Test against all sample projects in `input/`

## Input Files

- SoapUI project XML files go in `input/`
- External Groovy scripts go in `input/external_scripts/`
- Sample projects provided: `small_soapui_project.xml`, `Google-Maps-soapui-project.xml`, `Project-1-soapui-project.xml`

## Testing & Validation

**CRITICAL: Always test LLM connection first**:
```bash
python -m scripts.test_llm
```
This verifies your `.env` configuration and LLM provider connectivity before attempting documentation generation.

**No automated test suite exists yet** - validation is done through:
1. Running `test_llm.py` to verify LLM setup
2. Running parser on sample projects in `input/`
3. Comparing output documentation for correctness
4. Manual verification of XML→JSON→enriched transformations
5. Testing web UI by uploading sample projects

## Development Workflows

### Adding a New LLM Provider

1. Update `core/llm_client.py` to add provider-specific client initialization
2. Add provider configuration to `.env.example` (API key, base URL, model)
3. Update README.md LLM provider list
4. Test with `python -m scripts.test_llm`

### Modifying Layer 1 (XML→JSON Conversion)

- **File**: `core/xml_to_json.py`
- **Principle**: Never interpret, only preserve
- **Test**: Run on sample projects and verify no data loss in JSON output
- Changes here affect ALL downstream processing

### Modifying Layer 2 (Semantic Enrichment)

- **Files**: `core/json_filter.py`, extraction modules in `core/`
- **Principle**: Deterministic extraction only, no AI
- **Test**: Verify `output/layer2_enriched.json` structure
- Changes affect what context LLM receives

### Modifying Layer 3 (LLM Reasoning)

- **Files**: `prompts/*.txt`, `core/documentation_generator.py`, `core/testcase_llm_input_builder.py`
- **Principle**: Only change explanations/reasoning, not extraction
- **Test**: Compare generated documentation quality
- Safest layer to modify (doesn't affect structural extraction)

### Adding New Test Step Types

1. Update `core/teststep_extractor.py` to recognize new step type
2. Add intent detection logic in `core/intent_detector.py`
3. Update Pydantic models if needed (`models/teststep_model.py`)
4. Add handling in `core/testcase_llm_input_builder.py` for LLM context

### Running the Web UI

**Development mode**:
```bash
python app.py
# Opens on http://localhost:5000
```

**Production mode** (using Gunicorn):
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

The web UI uses the same three-layer architecture but:
- Runs processing in background threads
- Streams progress via Server-Sent Events (SSE)
- Only outputs DOCX format
- Creates `uploads/` folder for uploaded files
- Requires `templates/index.html` for UI

## Project File Structure

```
soapui-ai-docs/
├── core/              # Business logic (Layer 1-3 implementations)
├── models/            # Pydantic data models
├── documentation/     # Output formatters (Markdown, DOCX)
├── scripts/           # Entry point executables (CLI interface)
├── prompts/           # LLM prompt templates
├── utils/             # Shared utilities
├── config/            # YAML configuration files (legacy, prefer .env)
├── templates/         # Flask HTML templates for web UI
├── input/             # Place SoapUI XML projects here
│   └── external_scripts/  # External Groovy scripts
├── output/            # Generated documentation and JSON
├── uploads/           # Web UI file uploads (created by app.py)
├── .env               # Primary configuration (copy from .env.example)
├── app.py             # Flask web application (Path 3)
├── requirements.txt   # Python dependencies
└── venv/              # Virtual environment (created during setup)
```

## Final Output

The documentation generator produces a **single Markdown document** that:
- Any tester can understand (plain English explanations)
- Any developer can trust (grounded in actual project structure)
- Any manager can read (high-level summaries + details)

**Document sections**:
1. Project summary (test suites, test cases, enabled/disabled counts)
2. API inventory (endpoints, operations, queues)
3. External scripts listing
4. Per-suite breakdown with per-test-case explanations
5. Validation summaries (what is actually being checked)
6. Optional: Duplication warnings and redundancy analysis

## LLM Integration

The system supports **multiple LLM providers** configured via `.env`:

**Supported Providers**:
- **Ollama** (local, free) - Default: `mistral:latest`
- **OpenAI** - Models: `gpt-4o`, `gpt-4`, `gpt-3.5-turbo`
- **Anthropic** - Models: `claude-3-5-sonnet-20241022`, `claude-3-haiku`
- **Groq** (fast, free tier) - Model: `llama-3.1-70b-versatile`
- **Azure OpenAI** (enterprise)

The LLM client (`core/llm_client.py`) handles provider-specific formatting and expects streaming responses. All prompts use SYSTEM/USER/ASSISTANT role structure.

**System persona** (from `prompts/system.txt`): "You are a senior QA automation architect who analyzes structured technical data and explains what a testing project does in clear, plain English."

**Configuration**: Set `LLM_PROVIDER` in `.env` and provide corresponding API keys/endpoints.

## Common Development Workflows

### First-Time Setup
```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate (Windows)
venv\Scripts\activate
# Or (Linux/Mac)
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env to set INPUT_PROJECT_FILE and LLM provider

# 5. Test LLM connection
python -m scripts.test_llm

# 6. Run first documentation generation
python -m scripts.run_parser  # No LLM, fastest
```

### Typical Development Session
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Quick test without LLM
python -m scripts.run_parser

# Generate AI documentation (RECOMMENDED - ONE COMMAND!)
python -m scripts.run_pipeline              # ~30 min, generates BOTH MD + DOCX ⭐

# Fast re-run (after changing LLM settings)
python -m scripts.run_pipeline --skip-json  # Skip XML parsing, faster

# Manual DOCX conversion (if needed)
python -m scripts.md_to_docx                 # <1 sec

# For web UI development
python app.py                                # Now also uses fast converter!
```

### Switching Between Projects
Edit `.env` and change:
```env
INPUT_PROJECT_FILE=input/your-project.xml
```
Or use the web UI to upload different projects without configuration changes.

### Debugging Issues

**LLM not responding**:
```bash
# 1. Test connection
python -m scripts.test_llm

# 2. Check .env configuration
# Verify API keys, base URLs, model names

# 3. For Ollama: ensure service is running
ollama serve
```

**XML parsing errors**:
- SoapUI projects MUST use the `con:` namespace (`http://eviware.com/soapui/config`)
- All XPath queries require namespace registration
- Check `core/project_loader.py` for validation logic

**Missing output**:
- Check `output/` directory exists
- Verify write permissions
- Check logs (if logging is enabled)
- For web UI: check `uploads/` directory exists

## Future Possibilities

This architecture enables:
- **CI/CD plugin**: Auto-generate docs on commit
- **Change impact analysis**: What tests are affected by API changes?
- **Test redundancy detection**: Find duplicated test logic (partially implemented in LLM layer)
- **AI test optimization suggestions**: Identify gaps or inefficiencies
- **Coverage gaps detection**: What endpoints lack validation?
- **Migration assistant**: SoapUI → Postman/REST Assured conversion
- **Batch processing**: Process multiple projects in parallel
- **API endpoint catalog**: Track all APIs across multiple projects
