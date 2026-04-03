class ProjectAggregator:
    """
    Aggregates project-level insights from structure-agnostic intent models.
    No dependency on test steps.
    """

    def aggregate(self, suites):
        summary = {
            "test_suites_count": len(suites),
            "test_cases_total": 0,
            "test_cases_enabled": 0,
            "test_cases_disabled": 0,
            "unique_endpoints": set(),
            "unique_operations": set(),
            "unique_queues": set(),
            "external_scripts": set(),
        }

        for suite in suites:
            for tc in suite.test_cases:
                summary["test_cases_total"] += 1

                if tc.enabled:
                    summary["test_cases_enabled"] += 1
                else:
                    summary["test_cases_disabled"] += 1

                # External Groovy scripts
                for script in tc.external_scripts:
                    summary["external_scripts"].add(script)

                # Requests (future-safe)
                for req in getattr(tc, "requests", []):
                    endpoint = req.get("endpoint")
                    operation = req.get("operation")
                    queue = req.get("queue")

                    if endpoint:
                        summary["unique_endpoints"].add(endpoint)
                    if operation:
                        summary["unique_operations"].add(operation)
                    if queue:
                        summary["unique_queues"].add(queue)

        # Convert sets to sorted lists
        summary["unique_endpoints"] = sorted(summary["unique_endpoints"])
        summary["unique_operations"] = sorted(summary["unique_operations"])
        summary["unique_queues"] = sorted(summary["unique_queues"])
        summary["external_scripts"] = sorted(summary["external_scripts"])

        return summary
