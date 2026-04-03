from typing import List
import re


def extract_groovy_intent(script_content: str) -> List[str]:
    """
    Extracts high-level intent from Groovy scripts
    using deterministic pattern matching.
    """

    intents: List[str] = []

    patterns = {
        "ASSERT": r"assert\s+",
        "RESPONSE_VALIDATION": r"response|context\.response",
        "PROPERTY_ACCESS": r"context\.expand|getProperty",
        "SECURITY_CHECK": r"password|token|authorization",
        "DATA_EXTRACTION": r"JsonSlurper|XmlSlurper",
        "FAILURE_HANDLING": r"fail\(|throw\s+",
        "LOGGING": r"log\.|println"
    }

    for intent, pattern in patterns.items():
        if re.search(pattern, script_content, re.IGNORECASE):
            intents.append(intent)

    return intents
