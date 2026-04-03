"""
Layer 1: Postman Collection to JSON Converter

Converts Postman collection JSON format into the same normalized structure
as SoapUI projects, enabling unified Layer 2 processing.
"""

import json
from typing import Dict, Any, List
from pathlib import Path


class PostmanToJSONConverter:
    """
    Converts Postman collection format to normalized JSON structure
    compatible with the existing enrichment pipeline.
    """

    def __init__(self, file_path: str):
        """Initialize with Postman collection file path."""
        self.file_path = Path(file_path)
        self.collection = None

    def load(self) -> Dict[str, Any]:
        """Load Postman collection JSON."""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.collection = json.load(f)
        return self.collection

    def convert(self) -> Dict[str, Any]:
        """
        Convert Postman collection to normalized structure matching SoapUI format.

        Returns structure compatible with JSONStructureEnricher:
        {
            "project": {...},
            "test_suites": [...]
        }
        """
        if not self.collection:
            self.load()

        # Extract collection info
        info = self.collection.get('info', {})
        project_name = info.get('name', 'Untitled Collection')

        # Convert Postman items (folders/requests) to test suites
        test_suites = self._convert_items(self.collection.get('item', []))

        # Build normalized structure
        normalized = {
            "project": {
                "name": project_name,
                "type": "Postman Collection",
                "description": info.get('description', ''),
                "version": info.get('schema', 'unknown')
            },
            "test_suites": test_suites
        }

        return normalized

    def _convert_items(self, items: List[Dict[str, Any]], parent_name: str = None) -> List[Dict[str, Any]]:
        """
        Convert Postman items (folders/requests) to test suites.

        Postman structure:
        - Folders (groups) → Test Suites
        - Requests → Test Cases
        """
        test_suites = []

        for item in items:
            item_name = item.get('name', 'Untitled')

            # Check if this is a folder (has nested items) or a request
            if 'item' in item:
                # This is a folder - treat as test suite
                suite_name = f"{parent_name} / {item_name}" if parent_name else item_name

                # Recursively process nested items
                nested_items = item.get('item', [])
                test_cases = []
                nested_suites = []

                for nested_item in nested_items:
                    if 'item' in nested_item:
                        # Nested folder - create sub-suite
                        nested_suites.extend(self._convert_items([nested_item], suite_name))
                    else:
                        # Request - convert to test case
                        test_cases.append(self._convert_request_to_testcase(nested_item))

                # Create test suite
                if test_cases:
                    test_suites.append({
                        "name": suite_name,
                        "enabled": True,
                        "description": item.get('description', ''),
                        "test_cases": test_cases
                    })

                # Add nested suites
                test_suites.extend(nested_suites)

            else:
                # This is a standalone request - create a test suite with single test case
                if not parent_name:
                    test_suites.append({
                        "name": "Ungrouped Requests",
                        "enabled": True,
                        "test_cases": [self._convert_request_to_testcase(item)]
                    })

        return test_suites

    def _convert_request_to_testcase(self, request_item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Postman request to a test case."""
        request = request_item.get('request', {})

        # Handle both string and object URL formats
        url_data = request.get('url', '')
        if isinstance(url_data, dict):
            raw_url = url_data.get('raw', '')
            protocol = url_data.get('protocol', 'https')
            host = '.'.join(url_data.get('host', []))
            path = '/'.join(url_data.get('path', []))
            endpoint = f"{protocol}://{host}" if host else raw_url
            resource = f"/{path}" if path else ''
        else:
            # String URL
            raw_url = url_data
            # Try to split into endpoint and resource
            if '://' in raw_url:
                parts = raw_url.split('/', 3)
                endpoint = f"{parts[0]}//{parts[2]}" if len(parts) >= 3 else raw_url
                resource = f"/{parts[3]}" if len(parts) > 3 else ''
            else:
                endpoint = raw_url
                resource = ''

        method = request.get('method', 'GET')

        # Extract request body
        body_data = request.get('body', {})
        request_body = None
        if body_data:
            mode = body_data.get('mode', 'none')
            if mode == 'raw':
                request_body = body_data.get('raw', '')
            elif mode == 'formdata':
                request_body = str(body_data.get('formdata', []))
            elif mode == 'urlencoded':
                request_body = str(body_data.get('urlencoded', []))

        # Extract headers
        headers = []
        for header in request.get('header', []):
            if not header.get('disabled', False):
                headers.append({
                    "key": header.get('key', ''),
                    "value": header.get('value', '')
                })

        # Extract tests/assertions from event scripts
        assertions = self._extract_tests_from_events(request_item.get('event', []))

        # Extract pre-request scripts
        scripts = self._extract_scripts_from_events(request_item.get('event', []))

        # Build test steps
        test_steps = []

        # Add main request step
        request_step = {
            "name": f"{method} Request",
            "type": "restrequest",
            "enabled": True,
            "endpoint": endpoint,
            "method": method,
            "resource": resource,
            "assertions": assertions
        }

        if request_body:
            request_step["request_body"] = request_body

        if headers:
            request_step["headers"] = headers

        test_steps.append(request_step)

        # Add script steps if any
        test_steps.extend(scripts)

        return {
            "name": request_item.get('name', 'Untitled Request'),
            "enabled": True,
            "description": request_item.get('description', ''),
            "test_steps": test_steps
        }

    def _extract_tests_from_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract test assertions from Postman event scripts."""
        assertions = []

        for event in events:
            if event.get('listen') == 'test':
                script = event.get('script', {})
                exec_lines = script.get('exec', [])

                if exec_lines:
                    script_text = '\n'.join(exec_lines) if isinstance(exec_lines, list) else exec_lines

                    # Parse common Postman test patterns
                    assertions.extend(self._parse_postman_tests(script_text))

        return assertions

    def _parse_postman_tests(self, script: str) -> List[Dict[str, Any]]:
        """Parse Postman test script to extract assertions."""
        assertions = []

        # Common Postman test patterns
        patterns = {
            'pm.response.to.have.status': 'HTTP Status Code',
            'pm.expect(pm.response.code)': 'HTTP Status Code',
            'pm.response.to.be.ok': 'Response OK (2xx)',
            'pm.response.to.have.jsonBody': 'JSON Body Present',
            'pm.expect(jsonData': 'JSON Content Validation',
            'pm.response.to.have.header': 'Header Validation',
            'pm.response.responseTime': 'Response Time',
            'pm.expect(pm.response.text())': 'Response Text Validation',
        }

        lines = script.split('\n')
        for line in lines:
            line = line.strip()

            # Skip comments
            if line.startswith('//'):
                continue

            # Try to extract test name from pm.test()
            if 'pm.test(' in line:
                # Extract test name
                start = line.find('"') + 1
                end = line.find('"', start)
                if start > 0 and end > start:
                    test_name = line[start:end]
                else:
                    start = line.find("'") + 1
                    end = line.find("'", start)
                    test_name = line[start:end] if start > 0 and end > start else "Test Assertion"

                # Determine assertion type
                assertion_type = "Test Assertion"
                for pattern, atype in patterns.items():
                    if pattern in line:
                        assertion_type = atype
                        break

                assertions.append({
                    "name": test_name,
                    "type": assertion_type,
                    "script": line
                })

        # If no structured tests found but script exists, add generic assertion
        if not assertions and script.strip():
            assertions.append({
                "name": "Custom Test Script",
                "type": "JavaScript Test",
                "script": script[:200] + "..." if len(script) > 200 else script
            })

        return assertions

    def _extract_scripts_from_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract pre-request scripts as test steps."""
        scripts = []

        for event in events:
            if event.get('listen') == 'prerequest':
                script = event.get('script', {})
                exec_lines = script.get('exec', [])

                if exec_lines:
                    script_text = '\n'.join(exec_lines) if isinstance(exec_lines, list) else exec_lines

                    scripts.append({
                        "name": "Pre-request Script",
                        "type": "groovy",  # Use groovy type for compatibility
                        "enabled": True,
                        "script": script_text
                    })

        return scripts


def detect_format(file_path: str) -> str:
    """
    Auto-detect if file is SoapUI XML or Postman JSON.

    Returns: 'soapui', 'postman', or 'unknown'
    """
    file_path = Path(file_path)

    # Check extension first
    if file_path.suffix.lower() == '.xml':
        return 'soapui'
    elif file_path.suffix.lower() == '.json':
        # Check if it's Postman format
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check for Postman collection markers
            if 'info' in data and 'item' in data:
                schema = data.get('info', {}).get('schema', '')
                if 'postman' in schema.lower():
                    return 'postman'
                # Even without schema, if has info + item structure, likely Postman
                return 'postman'

        except:
            pass

    return 'unknown'
