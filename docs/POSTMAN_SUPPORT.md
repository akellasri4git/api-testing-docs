# Postman Collection Support

## Overview

The tool now supports **both SoapUI XML and Postman JSON** collections! 🎉

## Supported Formats

| Tool | Format | Extension | Example File |
|------|--------|-----------|--------------|
| **SoapUI** | XML | `.xml` | `project-soapui-project.xml` |
| **Postman** | JSON | `.json` | `collection.postman_collection.json` |

## How It Works

### Auto-Detection
The system automatically detects the format based on:
1. **File extension** (`.xml` vs `.json`)
2. **Content structure** (checks for Postman schema markers)

No manual format selection needed - just provide your file!

### Conversion Flow

**SoapUI Path:**
```
SoapUI XML → XMLToJSONConverter → Lossless JSON → JSONStructureEnricher → Normalized JSON → LLM Documentation
```

**Postman Path:**
```
Postman JSON → PostmanToJSONConverter → Normalized JSON → LLM Documentation
```

Both formats are normalized to the same structure, so Layer 2 and Layer 3 work identically!

## What Gets Extracted from Postman

### From Requests:
- ✅ HTTP Method (GET, POST, PUT, DELETE, etc.)
- ✅ Endpoint URLs (protocol, host, path)
- ✅ Headers
- ✅ Request body (raw, form-data, urlencoded)
- ✅ Query parameters
- ✅ Request description

### From Tests:
- ✅ `pm.test()` assertions
- ✅ Status code checks
- ✅ Response time validations
- ✅ JSON body validations
- ✅ Header validations
- ✅ Custom JavaScript test scripts

### From Structure:
- ✅ Folders → Test Suites
- ✅ Requests → Test Cases
- ✅ Pre-request scripts → Test Steps
- ✅ Collection metadata (name, description)

## Using with CLI

```bash
# Auto-detects SoapUI XML
python -m scripts.run_pipeline
# (with INPUT_PROJECT_FILE=input/soapui-project.xml in .env)

# Auto-detects Postman JSON
python -m scripts.run_pipeline
# (with INPUT_PROJECT_FILE=input/postman-collection.json in .env)
```

## Using with Web UI

1. Start the web server:
   ```bash
   python app.py
   ```

2. Open browser: http://localhost:5000

3. Upload either:
   - SoapUI XML file (`.xml`)
   - Postman collection JSON (`.json`)

4. Select LLM provider and model

5. Click "Generate Documentation"

The system automatically detects the format and processes accordingly!

## Example Output

For a Postman collection with:
- 2 folders (User Management, Product Catalog)
- 4 requests (Login, Get Profile, List Products, Create Product)

The tool generates:
- **Project Overview** with collection metadata
- **API Inventory** showing all endpoints
- **Test Suite Details** with AI-powered explanations for each request
- **Professional DOCX** with proper formatting

## Postman Test Script Parsing

The tool intelligently parses common Postman test patterns:

| Pattern | Detected As |
|---------|-------------|
| `pm.response.to.have.status(200)` | HTTP Status Code validation |
| `pm.expect(jsonData.token).to.exist` | JSON Content validation |
| `pm.response.to.have.header(...)` | Header validation |
| `pm.response.responseTime < 500` | Response Time validation |
| `pm.test("Custom test", ...)` | Custom Test Assertion |

## Sample Collection

A sample Postman collection is included:
- **File**: `input/sample-postman-collection.json`
- **Contains**: 2 test suites, 4 requests with assertions
- **Use**: Test the Postman support feature

## Differences from SoapUI

### What's Different:
- Postman collections are **pre-normalized** (no need for Layer 2 enrichment)
- Postman uses JavaScript tests (vs Groovy scripts in SoapUI)
- Postman has simpler structure (folders → requests vs testSuites → testCases → testSteps)

### What's the Same:
- Layer 3 LLM reasoning works identically
- Same DOCX output format
- Same AI-powered explanations
- Same professional documentation quality

## Technical Details

### New Module: `core/postman_to_json.py`

**Key Functions:**
- `detect_format(file_path)` - Auto-detects SoapUI vs Postman
- `PostmanToJSONConverter.convert()` - Converts Postman to normalized JSON
- `_parse_postman_tests(script)` - Extracts assertions from test scripts
- `_convert_request_to_testcase()` - Maps Postman requests to test cases

### Updated Modules:
- `scripts/run_pipeline.py` - Added format auto-detection
- `app.py` - Updated to support both formats
- `templates/index.html` - Updated UI to accept both `.xml` and `.json`

## Limitations

Current limitations for Postman collections:
- ❌ Collection-level variables not yet extracted
- ❌ Environment files not supported (coming soon)
- ❌ Dynamic variables (`{{variable}}`) shown as-is
- ❌ Chained requests dependencies not analyzed yet

These will be added in future updates based on user feedback!

## Next Steps

Potential future enhancements:
1. Bruno `.bru` file support
2. Insomnia workspace support
3. Thunder Client collection support
4. Environment variable extraction and documentation
5. Request chaining analysis

---

**Questions or Issues?** Please open a GitHub issue!
