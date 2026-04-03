"""
Generic JSON filter for LLM consumption.

Design principles:
- NO SoapUI assumptions
- NO hardcoded structures
- Keep semantic signal
- Remove noise
"""

from typing import Dict, Any, List
from copy import deepcopy
import re


IMPORTANT_TAG_KEYWORDS = {
    "test", "request", "assert", "script", "operation",
    "method", "endpoint", "resource", "property", "parameter"
}

IMPORTANT_ATTRIBUTE_KEYS = {
    "name", "type", "method", "path", "endpoint", "disabled"
}

IMPORTANT_TEXT_PATTERNS = [
    r"http[s]?://",
    r"\$\{.*?\}",
    r"<soap",
    r"<\?xml",
    r"assert",
    r"status",
    r"response",
    r"request"
]


class JSONSemanticFilter:
    def filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        filtered = deepcopy(data)
        result = self._filter_node(filtered["root"])
        return {"root": result} if result else {}

    def _filter_node(self, node: Dict[str, Any]) -> Dict[str, Any] | None:
        keep = self._is_important(node)

        filtered_children: List[Dict[str, Any]] = []
        for child in node.get("children", []):
            filtered_child = self._filter_node(child)
            if filtered_child:
                filtered_children.append(filtered_child)

        if keep or filtered_children:
            new_node = {
                "id": node.get("id"),
                "path": node.get("path"),
                "tag": node.get("tag")
            }

            if "attributes" in node:
                attrs = {
                    k: v for k, v in node["attributes"].items()
                    if k.lower() in IMPORTANT_ATTRIBUTE_KEYS
                }
                if attrs:
                    new_node["attributes"] = attrs

            if "text" in node:
                new_node["text"] = node["text"]

            if filtered_children:
                new_node["children"] = filtered_children

            return new_node

        return None

    def _is_important(self, node: Dict[str, Any]) -> bool:
        tag = node.get("tag", "").lower()
        if any(k in tag for k in IMPORTANT_TAG_KEYWORDS):
            return True

        for key in node.get("attributes", {}).keys():
            if key.lower() in IMPORTANT_ATTRIBUTE_KEYS:
                return True

        text = node.get("text", "")
        for pattern in IMPORTANT_TEXT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False
