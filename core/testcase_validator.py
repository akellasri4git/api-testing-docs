class TestCaseValidatorSummarizer:
    """
    Generates clear, human-readable explanation of test intent.
    """

    def summarize(self, testcase):
        lines = []

        # 1️⃣ What API is called
        if testcase.requests:
            req = testcase.requests[0]
            if req.get("operation"):
                lines.append(
                    f"This test calls the `{req['operation']}` operation."
                )
            elif req.get("endpoint"):
                lines.append(
                    f"This test sends a request to `{req['endpoint']}`."
                )

        # 2️⃣ What is validated
        if testcase.validations:
            lines.append("It validates that:")

            for v in testcase.validations:
                vtype = v.get("type", "").lower()

                if "xpath" in vtype:
                    lines.append("- The response XML structure is correct")
                elif "soap response" in vtype:
                    lines.append("- A valid SOAP response is returned")
                elif "contains" in vtype:
                    lines.append("- The response contains expected values")
                else:
                    lines.append("- The response meets expected conditions")

        return lines
