from typing import Dict
from lxml import etree


# Central place for all SoapUI namespaces
SOAPUI_NAMESPACES: Dict[str, str] = {
    "con": "http://eviware.com/soapui/config",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "soap": "http://schemas.xmlsoap.org/soap/envelope/",
    "soap12": "http://www.w3.org/2003/05/soap-envelope",
    "wsdl": "http://schemas.xmlsoap.org/wsdl/",
    "xsd": "http://www.w3.org/2001/XMLSchema",
}


def get_namespaces() -> Dict[str, str]:
    """
    Returns SoapUI XML namespaces for XPath usage.
    """
    return SOAPUI_NAMESPACES


def strip_namespace(tag: str) -> str:
    """
    Removes namespace from an XML tag.

    Example:
        {http://eviware.com/soapui/config}testCase -> testCase
    """
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def find_elements(
    root: etree._Element,
    xpath: str
) -> list[etree._Element]:
    """
    Namespace-aware XPath finder.

    Args:
        root: XML root element
        xpath: XPath using 'con:' prefix

    Returns:
        List of matching XML elements
    """
    return root.xpath(xpath, namespaces=SOAPUI_NAMESPACES)
