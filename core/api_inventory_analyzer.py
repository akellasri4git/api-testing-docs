"""
API Inventory Analyzer

Extracts and aggregates:
- Unique endpoints
- Unique operations (SOAP operations, REST resources)
- Unique queues (JMS queues)
- External scripts
- Test case usage statistics
"""

from typing import Dict, List, Set, Any
from collections import defaultdict
from urllib.parse import urlparse


class APIInventoryAnalyzer:
    """Analyzes enriched JSON to extract API inventory and usage statistics"""

    def __init__(self, enriched_data: Dict[str, Any]):
        self.data = enriched_data
        self.endpoints = defaultdict(list)  # endpoint -> list of test cases using it
        self.operations = defaultdict(list)  # operation -> list of test cases
        self.queues = defaultdict(list)  # queue -> list of test cases
        self.resources = defaultdict(list)  # REST resource -> list of test cases
        self.external_scripts = defaultdict(list)  # script -> list of test cases
        self.methods = defaultdict(list)  # HTTP method -> list of test cases

    def analyze(self) -> Dict[str, Any]:
        """
        Perform complete analysis and return inventory summary

        Returns:
            Dictionary with all inventory data
        """
        test_suites = self.data.get("test_suites", [])

        for suite in test_suites:
            suite_name = suite.get("name", "Unknown Suite")

            for test_case in suite.get("test_cases", []):
                tc_name = test_case.get("name", "Unknown Test Case")
                tc_enabled = test_case.get("enabled", True)
                tc_ref = f"{suite_name} > {tc_name}"

                # Analyze test steps
                for step in test_case.get("test_steps", []) or test_case.get("steps", []):
                    self._analyze_step(step, tc_ref, tc_enabled)

        return self._build_summary()

    def _analyze_step(self, step: Dict[str, Any], test_case_ref: str, enabled: bool):
        """Analyze a single test step"""
        step_type = step.get("type", "")

        # Extract endpoint
        endpoint = step.get("endpoint")
        if endpoint:
            self.endpoints[endpoint].append({
                "test_case": test_case_ref,
                "enabled": enabled,
                "step_name": step.get("name", "Unnamed Step")
            })

        # Extract HTTP method
        method = step.get("method")
        if method:
            self.methods[method].append({
                "test_case": test_case_ref,
                "enabled": enabled,
                "endpoint": endpoint
            })

        # Extract REST resource
        resource = step.get("resource")
        if resource:
            self.resources[resource].append({
                "test_case": test_case_ref,
                "enabled": enabled,
                "endpoint": endpoint
            })

        # Extract SOAP operation
        operation = step.get("operation")
        if operation:
            self.operations[operation].append({
                "test_case": test_case_ref,
                "enabled": enabled,
                "endpoint": endpoint
            })

        # Extract JMS queue
        if step_type in ["jms", "amf", "amfRequest"]:
            queue = step.get("queue") or step.get("destination") or step.get("send_queue")
            if queue:
                self.queues[queue].append({
                    "test_case": test_case_ref,
                    "enabled": enabled
                })

        # Extract Groovy script references
        script_ref = step.get("script_reference") or step.get("scriptFile")
        if script_ref:
            self.external_scripts[script_ref].append({
                "test_case": test_case_ref,
                "enabled": enabled,
                "step_name": step.get("name", "Unnamed Step")
            })

    def _build_summary(self) -> Dict[str, Any]:
        """Build final summary dictionary"""
        return {
            "endpoints": self._summarize_endpoints(),
            "operations": self._summarize_operations(),
            "queues": self._summarize_queues(),
            "resources": self._summarize_resources(),
            "methods": self._summarize_methods(),
            "external_scripts": self._summarize_external_scripts(),
            "statistics": self._calculate_statistics()
        }

    def _summarize_endpoints(self) -> List[Dict[str, Any]]:
        """Summarize endpoints with usage counts"""
        summary = []
        for endpoint, usages in sorted(self.endpoints.items()):
            enabled_count = sum(1 for u in usages if u["enabled"])
            disabled_count = len(usages) - enabled_count

            # Parse domain from endpoint
            try:
                parsed = urlparse(endpoint)
                domain = parsed.netloc or endpoint
            except:
                domain = endpoint

            summary.append({
                "endpoint": endpoint,
                "domain": domain,
                "total_usages": len(usages),
                "enabled_usages": enabled_count,
                "disabled_usages": disabled_count,
                "test_cases": sorted(list(set(u["test_case"] for u in usages)))
            })

        return summary

    def _summarize_operations(self) -> List[Dict[str, Any]]:
        """Summarize SOAP operations"""
        summary = []
        for operation, usages in sorted(self.operations.items()):
            enabled_count = sum(1 for u in usages if u["enabled"])

            summary.append({
                "operation": operation,
                "total_usages": len(usages),
                "enabled_usages": enabled_count,
                "test_cases": sorted(list(set(u["test_case"] for u in usages)))
            })

        return summary

    def _summarize_queues(self) -> List[Dict[str, Any]]:
        """Summarize JMS queues"""
        summary = []
        for queue, usages in sorted(self.queues.items()):
            enabled_count = sum(1 for u in usages if u["enabled"])

            summary.append({
                "queue": queue,
                "total_usages": len(usages),
                "enabled_usages": enabled_count,
                "test_cases": sorted(list(set(u["test_case"] for u in usages)))
            })

        return summary

    def _summarize_resources(self) -> List[Dict[str, Any]]:
        """Summarize REST resources"""
        summary = []
        for resource, usages in sorted(self.resources.items()):
            enabled_count = sum(1 for u in usages if u["enabled"])

            summary.append({
                "resource": resource,
                "total_usages": len(usages),
                "enabled_usages": enabled_count,
                "test_cases": sorted(list(set(u["test_case"] for u in usages)))
            })

        return summary

    def _summarize_methods(self) -> List[Dict[str, Any]]:
        """Summarize HTTP methods"""
        summary = []
        for method, usages in sorted(self.methods.items()):
            enabled_count = sum(1 for u in usages if u["enabled"])

            summary.append({
                "method": method,
                "total_usages": len(usages),
                "enabled_usages": enabled_count,
                "unique_endpoints": len(set(u["endpoint"] for u in usages if u.get("endpoint")))
            })

        return summary

    def _summarize_external_scripts(self) -> List[Dict[str, Any]]:
        """Summarize external Groovy scripts"""
        summary = []
        for script, usages in sorted(self.external_scripts.items()):
            enabled_count = sum(1 for u in usages if u["enabled"])

            summary.append({
                "script": script,
                "total_usages": len(usages),
                "enabled_usages": enabled_count,
                "test_cases": sorted(list(set(u["test_case"] for u in usages)))
            })

        return summary

    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate overall statistics"""
        return {
            "total_unique_endpoints": len(self.endpoints),
            "total_unique_operations": len(self.operations),
            "total_unique_queues": len(self.queues),
            "total_unique_resources": len(self.resources),
            "total_external_scripts": len(self.external_scripts),
            "http_methods_used": list(self.methods.keys())
        }


def format_inventory_markdown(inventory: Dict[str, Any]) -> str:
    """
    Format inventory data as markdown

    Args:
        inventory: Inventory data from APIInventoryAnalyzer.analyze()

    Returns:
        Formatted markdown string
    """
    lines = []

    lines.append("## API Inventory\n")
    lines.append("*Unique endpoints, operations, and resources detected in this project*\n")

    # Statistics Summary
    stats = inventory.get("statistics", {})
    lines.append("### Summary\n")
    lines.append(f"- **Unique Endpoints:** {stats.get('total_unique_endpoints', 0)}")
    lines.append(f"- **Unique Operations:** {stats.get('total_unique_operations', 0)}")
    lines.append(f"- **Unique Queues:** {stats.get('total_unique_queues', 0)}")
    lines.append(f"- **External Scripts:** {stats.get('total_external_scripts', 0)}")

    http_methods = stats.get('http_methods_used', [])
    if http_methods:
        lines.append(f"- **HTTP Methods Used:** {', '.join(sorted(http_methods))}")

    lines.append("")

    # Endpoints
    endpoints = inventory.get("endpoints", [])
    if endpoints:
        lines.append("### Endpoints\n")
        for ep in endpoints:
            lines.append(f"#### `{ep['endpoint']}`")
            lines.append(f"- **Total Usages:** {ep['total_usages']} ({ep['enabled_usages']} enabled, {ep['disabled_usages']} disabled)")
            lines.append(f"- **Used in Test Cases:**")
            for tc in ep['test_cases']:
                lines.append(f"  - {tc}")
            lines.append("")

    # Operations
    operations = inventory.get("operations", [])
    if operations:
        lines.append("### SOAP Operations\n")
        for op in operations:
            lines.append(f"#### `{op['operation']}`")
            lines.append(f"- **Total Usages:** {op['total_usages']} ({op['enabled_usages']} enabled)")
            lines.append(f"- **Used in Test Cases:**")
            for tc in op['test_cases']:
                lines.append(f"  - {tc}")
            lines.append("")

    # Resources
    resources = inventory.get("resources", [])
    if resources:
        lines.append("### REST Resources\n")
        for res in resources:
            lines.append(f"#### `{res['resource']}`")
            lines.append(f"- **Total Usages:** {res['total_usages']} ({res['enabled_usages']} enabled)")
            lines.append(f"- **Used in Test Cases:**")
            for tc in res['test_cases']:
                lines.append(f"  - {tc}")
            lines.append("")

    # Queues
    queues = inventory.get("queues", [])
    if queues:
        lines.append("### JMS Queues\n")
        for q in queues:
            lines.append(f"#### `{q['queue']}`")
            lines.append(f"- **Total Usages:** {q['total_usages']} ({q['enabled_usages']} enabled)")
            lines.append(f"- **Used in Test Cases:**")
            for tc in q['test_cases']:
                lines.append(f"  - {tc}")
            lines.append("")

    # External Scripts
    scripts = inventory.get("external_scripts", [])
    if scripts:
        lines.append("### External Scripts\n")
        lines.append("*Groovy scripts referenced from test steps*\n")
        for script in scripts:
            lines.append(f"#### `{script['script']}`")
            lines.append(f"- **Total Usages:** {script['total_usages']} ({script['enabled_usages']} enabled)")
            lines.append(f"- **Used in Test Cases:**")
            for tc in script['test_cases']:
                lines.append(f"  - {tc}")
            lines.append("")

    lines.append("---\n")

    return "\n".join(lines)
