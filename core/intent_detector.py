class IntentDetector:
    """
    Detects semantic intent from SoapUI XML elements.
    Structure-agnostic.
    """

    @staticmethod
    def is_request(elem) -> bool:
        tag = elem.tag.lower()
        return (
            "restrequest" in tag
            or "request" in tag
        )

    @staticmethod
    def extract_request(elem) -> dict:
        endpoint = None
        operation = None
        method = None

        for child in elem.iter():
            tag = child.tag.lower()

            if tag.endswith("endpoint") and child.text:
                endpoint = child.text.strip()

            if tag.endswith("operation") and child.text:
                operation = child.text.strip()

            if tag.endswith("methodname"):
                method = child.text.strip()

        return {
            "endpoint": endpoint,
            "operation": operation,
            "method": method
        }

    @staticmethod
    def is_assertion(elem) -> bool:
        return elem.tag.lower().endswith("assertion")

    @staticmethod
    def extract_validation(elem) -> dict:
        return {
            "type": elem.attrib.get("type", "UNKNOWN"),
            "name": elem.attrib.get("name", ""),
            "raw": (elem.text or "").strip()
        }
