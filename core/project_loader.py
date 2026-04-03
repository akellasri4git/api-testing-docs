from pathlib import Path
from typing import Union
import logging

from lxml import etree


logger = logging.getLogger(__name__)


class SoapUIProjectLoader:
    """
    Responsible ONLY for:
    - Validating SoapUI project file
    - Loading XML safely
    - Returning parsed XML root

    No extraction logic belongs here.
    """

    def __init__(self, project_path: Union[str, Path]):
        self.project_path = Path(project_path)

    def validate_project_file(self) -> None:
        """
        Ensures the SoapUI project file exists and is readable.
        """
        logger.info("Validating SoapUI project file")

        if not self.project_path.exists():
            raise FileNotFoundError(
                f"SoapUI project file not found: {self.project_path}"
            )

        if not self.project_path.is_file():
            raise ValueError(
                f"Provided path is not a file: {self.project_path}"
            )

        if self.project_path.suffix.lower() != ".xml":
            raise ValueError(
                f"SoapUI project must be an XML file: {self.project_path}"
            )

        logger.info("SoapUI project file validation successful")

    def load(self) -> etree._Element:
        """
        Loads and parses the SoapUI XML project.

        Returns:
            lxml.etree._Element: Root XML element
        """
        self.validate_project_file()

        logger.info("Loading SoapUI project XML")

        try:
            parser = etree.XMLParser(
                remove_comments=False,
                recover=False,
                huge_tree=True
            )

            tree = etree.parse(str(self.project_path), parser)
            root = tree.getroot()

        except etree.XMLSyntaxError as exc:
            raise ValueError(
                f"Invalid XML structure in SoapUI project: {exc}"
            ) from exc

        logger.info("SoapUI project XML loaded successfully")
        return root
