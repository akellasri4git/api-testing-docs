"""
Flask Web Application for SoapUI Documentation Generator
Simple, minimalist UI for uploading projects and generating DOCX docs
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename
import threading
from queue import Queue

# Import our existing modules
from core.xml_to_json import XMLToJSONConverter
from core.postman_to_json import PostmanToJSONConverter, detect_format
from core.json_enricher import JSONStructureEnricher
from core.json_filter import JSONSemanticFilter
from core.llm_client import LLMClient
from core.testcase_llm_input_builder import TestCaseLLMInputBuilder
from core.prompt_loader import PromptLoader
from core.api_inventory_analyzer import APIInventoryAnalyzer, format_inventory_markdown
from scripts.md_to_docx import MarkdownToDocxConverter
from scripts.md_to_pdf import MarkdownToPdfConverter

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure folders exist
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(exist_ok=True)

# Global dictionary to store progress for each job
progress_tracker = {}


def allowed_file(filename):
    """Check if file is XML or JSON"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ['xml', 'json']


def generate_documentation_task(job_id, file_path, provider, model, document_type, progress_queue):
    """
    Background task to generate documentation with progress updates
    Uses fast MD→DOCX conversion (same as CLI pipeline)
    Supports both SoapUI XML and Postman JSON
    """
    try:
        # Step 1: Auto-detect format and convert (20%)
        progress_queue.put({'job_id': job_id, 'progress': 10, 'message': 'Detecting file format...'})
        time.sleep(0.5)

        # Detect format
        file_format = detect_format(file_path)

        if file_format == 'postman':
            progress_queue.put({'job_id': job_id, 'progress': 15, 'message': 'Loading Postman collection...'})
            converter = PostmanToJSONConverter(file_path)
            raw_json = converter.convert()
            progress_queue.put({'job_id': job_id, 'progress': 20, 'message': 'Parsing Postman structure...'})
        elif file_format == 'soapui':
            progress_queue.put({'job_id': job_id, 'progress': 15, 'message': 'Loading SoapUI XML...'})
            converter = XMLToJSONConverter(file_path)
            raw_json = converter.convert()
            progress_queue.put({'job_id': job_id, 'progress': 20, 'message': 'Parsing XML structure...'})
        else:
            raise ValueError("Unsupported file format. Please upload SoapUI XML or Postman JSON collection.")

        # Step 2: Enrich structure (30%)
        progress_queue.put({'job_id': job_id, 'progress': 30, 'message': 'Extracting test cases...'})

        # Check if already enriched (Postman format comes pre-normalized)
        if "test_suites" in raw_json and "project" in raw_json:
            enriched_json = raw_json
        else:
            enricher = JSONStructureEnricher()
            enriched_json = enricher.enrich(raw_json)

        # Step 3: Initialize LLM (50%)
        progress_queue.put({'job_id': job_id, 'progress': 50, 'message': f'Initializing {provider.upper()} AI...'})

        # Override provider from UI
        os.environ['LLM_PROVIDER'] = provider
        if model:
            if provider == 'groq':
                os.environ['GROQ_MODEL'] = model
            elif provider == 'ollama':
                os.environ['OLLAMA_MODEL'] = model
            elif provider == 'openai':
                os.environ['OPENAI_MODEL'] = model

        llm = LLMClient()

        # Step 4: Generate Markdown documentation (50% - 90%)
        progress_queue.put({'job_id': job_id, 'progress': 60, 'message': 'Generating AI summaries...'})

        # Load system prompt
        try:
            system_prompt = PromptLoader.load("prompts/system.txt")
        except:
            system_prompt = "You are a senior QA automation architect who explains test projects clearly."

        # Generate markdown
        docs = []
        docs.append("# SoapUI Project Documentation")
        docs.append("*Generated using AI-powered analysis*\n")

        # Project summary
        project_info = enriched_json.get("project", {})
        project_name = project_info.get('name', 'Unknown')
        docs.append("## Project Overview\n")
        docs.append(f"**Project Name:** {project_name}\n")

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

        # API Inventory
        inventory_analyzer = APIInventoryAnalyzer(enriched_json)
        inventory = inventory_analyzer.analyze()
        inventory_markdown = format_inventory_markdown(inventory)
        docs.append(inventory_markdown)

        # Per-suite documentation
        docs.append("## Test Suite Details\n")
        docs.append("*Detailed analysis of each test case with AI-powered explanations*\n")

        current_case = 0
        for suite in test_suites:
            suite_name = suite.get("name", "Unnamed Suite")
            docs.append(f"### Test Suite: {suite_name}\n")

            for tc in suite.get("test_cases", []):
                if not tc.get("enabled", True):
                    continue

                current_case += 1
                progress_percent = 60 + int((current_case / enabled_cases) * 30)
                progress_queue.put({
                    'job_id': job_id,
                    'progress': progress_percent,
                    'message': f'Analyzing test case {current_case}/{enabled_cases}...'
                })

                tc_name = tc.get("name", "Unnamed TestCase")
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
                    docs.append(f"*[Error generating explanation: {e}]*\n")
                    docs.append("---\n")

        # Save Markdown
        progress_queue.put({'job_id': job_id, 'progress': 90, 'message': 'Saving Markdown...'})
        markdown_content = "\n".join(docs)
        markdown_filename = f"{job_id}_documentation.md"
        markdown_path = Path(app.config['OUTPUT_FOLDER']) / markdown_filename
        markdown_path.write_text(markdown_content, encoding='utf-8')

        # Step 5: Convert Markdown to selected format (95%)
        if document_type.lower() == 'pdf':
            progress_queue.put({'job_id': job_id, 'progress': 95, 'message': 'Converting to PDF document...'})

            # Create meaningful filename: Understanding_Document_<ProjectName>_<Timestamp>.pdf
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Sanitize project name for filename
            safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_project_name = safe_project_name.replace(' ', '_')
            pdf_filename = f"Understanding_Document_{safe_project_name}_{timestamp}.pdf"
            pdf_path = Path(app.config['OUTPUT_FOLDER']) / pdf_filename

            pdf_converter = MarkdownToPdfConverter(str(markdown_path))
            pdf_converter.convert(str(pdf_path))

            progress_queue.put({
                'job_id': job_id,
                'progress': 100,
                'message': 'Documentation generated successfully! ⚡',
                'download_url': f'/download/{pdf_filename}',
                'status': 'completed'
            })
        else:  # Default to DOCX
            progress_queue.put({'job_id': job_id, 'progress': 95, 'message': 'Converting to Word document...'})

            # Create meaningful filename: Understanding_Document_<ProjectName>_<Timestamp>.docx
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Sanitize project name for filename
            safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_project_name = safe_project_name.replace(' ', '_')
            docx_filename = f"Understanding_Document_{safe_project_name}_{timestamp}.docx"
            docx_path = Path(app.config['OUTPUT_FOLDER']) / docx_filename

            md_converter = MarkdownToDocxConverter(str(markdown_path))
            md_converter.convert(str(docx_path))

            progress_queue.put({
                'job_id': job_id,
                'progress': 100,
                'message': 'Documentation generated successfully! ⚡',
                'download_url': f'/download/{docx_filename}',
                'status': 'completed'
            })

    except Exception as e:
        progress_queue.put({
            'job_id': job_id,
            'progress': 0,
            'message': f'Error: {str(e)}',
            'status': 'error'
        })


@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start processing"""

    # Validate file
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Only XML (SoapUI) or JSON (Postman) files are allowed'}), 400

    # Get provider, model, and document type
    provider = request.form.get('provider', 'groq').lower()
    model = request.form.get('model', '')
    document_type = request.form.get('document_type', 'docx').lower()

    # Save uploaded file
    filename = secure_filename(file.filename)
    file_ext = Path(filename).suffix  # Get original extension (.xml or .json)
    job_id = f"{int(time.time())}_{Path(filename).stem}"
    filepath = Path(app.config['UPLOAD_FOLDER']) / f"{job_id}{file_ext}"
    file.save(str(filepath))

    # Create progress queue for this job
    progress_queue = Queue()
    progress_tracker[job_id] = progress_queue

    # Start background processing
    thread = threading.Thread(
        target=generate_documentation_task,
        args=(job_id, str(filepath), provider, model, document_type, progress_queue)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'job_id': job_id, 'message': 'Processing started'})


@app.route('/progress/<job_id>')
def progress(job_id):
    """Server-Sent Events endpoint for real-time progress with keep-alive"""

    def generate():
        if job_id not in progress_tracker:
            yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
            return

        progress_queue = progress_tracker[job_id]
        last_progress = 0

        while True:
            try:
                # Get progress update (block for max 15 seconds)
                update = progress_queue.get(timeout=15)
                last_progress = update.get('progress', last_progress)
                yield f"data: {json.dumps(update)}\n\n"

                # If completed or error, stop streaming
                if update.get('status') in ['completed', 'error']:
                    # Cleanup
                    del progress_tracker[job_id]
                    break

            except:
                # Timeout - send keep-alive heartbeat to maintain connection
                # This allows processing to continue for hours if needed
                heartbeat = {
                    'job_id': job_id,
                    'progress': last_progress,
                    'message': 'Processing continues...',
                    'heartbeat': True
                }
                yield f"data: {json.dumps(heartbeat)}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/download/<filename>')
def download_file(filename):
    """Download generated DOCX file"""
    filepath = Path(app.config['OUTPUT_FOLDER']) / filename

    if not filepath.exists():
        return jsonify({'error': 'File not found'}), 404

    # Filename already has proper format, use it as-is
    return send_file(
        str(filepath),
        as_attachment=True,
        download_name=filename
    )


@app.route('/providers')
def get_providers():
    """Get available LLM providers and models"""
    providers = {
        'groq': {
            'name': 'Groq (Fast)',
            'models': [
                'llama-3.3-70b-versatile',
                'llama-3.1-70b-versatile',
                'mixtral-8x7b-32768'
            ],
            'default': 'llama-3.3-70b-versatile',
            'speed': 'Fast (10-15 sec)',
            'security': 'Cloud'
        },
        'ollama': {
            'name': 'Ollama (Local)',
            'models': [
                'llama3.1:8b',
                'llama3.1:70b',
                'mistral:latest',
                'codellama:latest'
            ],
            'default': 'llama3.1:8b',
            'speed': 'Slow (20-30 min)',
            'security': '100% Local'
        },
        'openai': {
            'name': 'OpenAI',
            'models': [
                'gpt-4o',
                'gpt-4o-mini',
                'gpt-4-turbo'
            ],
            'default': 'gpt-4o-mini',
            'speed': 'Fast (15-20 sec)',
            'security': 'Cloud'
        },
        'anthropic': {
            'name': 'Anthropic Claude',
            'models': [
                'claude-3-5-sonnet-20241022',
                'claude-3-opus-20240229',
                'claude-3-sonnet-20240229'
            ],
            'default': 'claude-3-5-sonnet-20241022',
            'speed': 'Fast (20-25 sec)',
            'security': 'Cloud'
        }
    }

    return jsonify(providers)


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 API Testing AI Documentation Generator")
    print("=" * 60)
    print("📍 Open in browser: http://localhost:5000")
    print("📋 Supports: SoapUI XML & Postman JSON")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
