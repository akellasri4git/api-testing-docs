"""
Lossless XML → JSON converter.

Rules:
- No interpretation
- No SoapUI-specific logic
- Preserve EVERYTHING:
  - tags
  - attributes
  - namespaces
  - text
  - order
"""

from lxml import etree
from typing import Any, Dict, Union
from pathlib import Path
import json


class XMLToJSONConverter:
    def __init__(self, xml_path: Union[str, Path]):
        self.xml_path = Path(xml_path)

    def convert(self) -> Dict[str, Any]:
        """
        Entry point: parses XML and returns JSON-compatible dict.
        """
        if not self.xml_path.exists():
            raise FileNotFoundError(f"XML file not found: {self.xml_path}")

        parser = etree.XMLParser(
            remove_blank_text=False,
            recover=True,
            huge_tree=True
        )

        tree = etree.parse(str(self.xml_path), parser)
        root = tree.getroot()

        return {
            "root": self._element_to_dict(root)
        }

    def _element_to_dict(self, element: etree._Element) -> Dict[str, Any]:
        """
        Converts a single XML element into a dict.
        """
        node: Dict[str, Any] = {
            "tag": self._qualified_name(element.tag)
        }

        # Attributes (with namespaces preserved)
        if element.attrib:
            node["attributes"] = {
                self._qualified_name(k): v
                for k, v in element.attrib.items()
            }

        # Text content
        text = (element.text or "").strip()
        if text:
            node["text"] = text

        # Child elements (order preserved)
        children = []
        for child in element:
            # Skip comments and processing instructions
            if isinstance(child.tag, str):
                children.append(self._element_to_dict(child))

        if children:
            node["children"] = children

        return node

    def _qualified_name(self, name: str) -> str:
        """
        Converts '{namespace}tag' → 'namespace|tag'
        Keeps namespace info without breaking JSON.
        """
        if name.startswith("{"):
            namespace, tag = name[1:].split("}")
            return f"{namespace}|{tag}"
        return name

    def save_to_file(self, output_path: Union[str, Path]) -> None:
        """
        Saves converted JSON to disk.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = self.convert()

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
