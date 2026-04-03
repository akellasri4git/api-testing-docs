# API Testing AI Documentation Generator

An AI-powered tool that converts SoapUI XML and Postman JSON projects into human-readable documentation.

## What This Does

**Problem:** API testing projects (SoapUI, Postman) are hard to understand, inconsistent across teams, and poorly documented.

**Solution:** This tool answers: *"I've never seen this testing project before — tell me what it does."*

**Input:**
- SoapUI XML projects (any structure, any version)
- Postman JSON collections (v2.0+)

**Output:** Professional DOCX documentation explaining what the tests do, how they work, and what they validate

## Architecture: Three Layers

This is not a traditional parser. It's a **structure-aware + LLM-reasoning system**.

```
Layer 1: Lossless Preservation  →  Layer 2: Semantic Enrichment  →  Layer 3: LLM Reasoning
(XML → JSON, no data loss)         (Extract structure)                (AI explanations)
```

### Layer 1: XML → Raw JSON (Lossless)
- Converts entire SoapUI XML to JSON
- Preserves all tags, attributes, namespaces, hierarchy
- No interpretation, no assumptions
- Makes XML data LLM-friendly

### Layer 2: Semantic Enrichment (Deterministic)
- Extracts SoapUI structure: projects, test suites, test cases, test steps
- Identifies endpoints, operations, assertions, scripts
- Still deterministic - no AI guessing
- Creates clean, normalized JSON

### Layer 3: LLM Reasoning (AI-Powered)
- Per-test-case AI analysis
- Explains purpose, validates behavior, identifies duplications
- Natural language explanations
- Human-quality documentation

## Supported Formats

| Tool | Format | Extension | Auto-Detected |
|------|--------|-----------|---------------|
| **SoapUI** | XML | `.xml` | ✅ Yes |
| **Postman** | JSON | `.json` | ✅ Yes |

The tool automatically detects the format - just provide your file!

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Edit `.env` file to configure:

```env
# Choose your testing project (SoapUI XML or Postman JSON)
INPUT_PROJECT_FILE=input/Google-Maps-soapui-project.xml
# OR
INPUT_PROJECT_FILE=input/sample-postman-collection.json

# Choose LLM provider (local or cloud)
LLM_PROVIDER=ollama

# For local (free) - requires Ollama
OLLAMA_MODEL=mistral:latest

# OR for cloud (requires API key)
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your-key-here
# OPENAI_MODEL=gpt-4o-mini
```

**Available LLM Providers:**
- **Ollama** (local, free)
- **OpenAI** (GPT-4, GPT-4o, GPT-3.5)
- **Anthropic** (Claude 3.5 Sonnet, Haiku)
- **Groq** (fast, free tier)
- **Azure OpenAI** (enterprise)

See [LLM_CONFIGURATION.md](LLM_CONFIGURATION.md) for detailed setup.

### Option 1: Direct Parser (No LLM - Fast)

Use this if you don't have Ollama or want quick results:

```bash
python -m scripts.run_parser
```

Output: `output/documentation.md`

### Option 2: AI-Powered Documentation

For AI-enhanced explanations:

```bash
# If using Ollama (local)
# 1. Install Ollama from https://ollama.com
# 2. Pull a model: ollama pull mistral:latest

# Run the three-layer pipeline
python -m scripts.xml_to_json_runner
python -m scripts.generate_docs
```

Outputs:
- `output/layer1_raw.json` - Lossless XML→JSON
- `output/layer2_enriched.json` - Semantic structure
- `output/llm_documentation.md` - AI-enhanced docs

**Cloud Providers:** If using OpenAI/Anthropic/Groq, just set your API key in `.env` - no local installation needed!

## Project Structure

```
soapui-ai-docs/
├── core/                   # Business logic (Layers 1-3)
├── models/                 # Pydantic data models
├── documentation/          # Markdown output formatters
├── scripts/                # 🚀 Entry point executables
│   ├── run_pipeline.py    # ⭐ Unified pipeline (recommended)
│   ├── md_to_docx.py      # ⭐ Fast MD→DOCX converter (<1 sec)
│   ├── run_parser.py      # Direct parser (no LLM)
│   ├── test_llm.py        # Test LLM connectivity
│   └── ...
├── prompts/                # LLM prompt templates
├── utils/                  # Shared utilities
├── docs/                   # 📚 Additional documentation
│   ├── README.md
│   ├── LLM_CONFIGURATION.md
│   └── WEB_UI_GUIDE.md
├── input/                  # 📥 Place SoapUI XML projects here
├── output/                 # 📤 Generated documentation
├── templates/              # Flask HTML templates (web UI)
├── app.py                  # 🌐 Web UI application
├── README.md               # This file
├── CLAUDE.md               # Developer guide (for Claude Code)
├── .env                    # ⚙️ Configuration
└── requirements.txt        # Python dependencies
```

## Configuration Files

All configuration is now in `.env` file:

```env
# Project Selection
INPUT_PROJECT_FILE=input/your-project.xml

# LLM Provider
LLM_PROVIDER=ollama|openai|anthropic|groq|azure

# Provider-specific settings
OLLAMA_MODEL=mistral:latest
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o-mini

# Generation parameters
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=600
```

See `.env.example` for all available options.

## How It Works

### The LLM Does:
- Explain test purpose in plain English
- Summarize validations and business logic
- Detect duplicate tests
- Provide context and clarity

### The LLM Does NOT Do:
- Parse XML/JSON
- Count test cases
- Extract endpoints or assertions
- Structural discovery

> **Key Principle:** All structural extraction is deterministic. AI only adds human-readable explanations.

## Why This Design is Correct

✅ **Project-agnostic:** No hardcoded SoapUI schemas
✅ **Version-independent:** Works with any SoapUI version
✅ **Future-proof:** Lossless preservation means no data loss
✅ **Scalable:** Per-test isolation enables parallel processing
✅ **Safe:** Separates deterministic work from probabilistic AI

## Future Possibilities

- CI/CD plugin (auto-generate docs on commit)
- Change impact analysis
- Test redundancy detection
- Coverage gap analysis
- Migration assistant (SoapUI → Postman/REST Assured)

## Contributing

This project uses a clean three-layer architecture. When contributing:

1. **Layer 1** changes should never interpret data
2. **Layer 2** changes should be deterministic and project-agnostic
3. **Layer 3** changes should only affect LLM prompts/reasoning

See `CLAUDE.md` for detailed architecture guidance.

## License

MIT

## Support

For issues or questions, please open a GitHub issue.
