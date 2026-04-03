from pathlib import Path
from typing import Dict, List

from utils.groovy_utils import extract_groovy_intent


class ScriptReferenceResolver:
    """
    Loads external Groovy scripts and extracts their intent.
    """

    def __init__(self, scripts_root: Path):
        self.scripts_root = scripts_root

    def resolve(self, script_paths: List[str]) -> Dict[str, List[str]]:
        """
        Returns script path → intent list
        """
        resolved = {}

        for script_path in script_paths:
            full_path = self.scripts_root / script_path

            if not full_path.exists():
                resolved[script_path] = ["SCRIPT_NOT_FOUND"]
                continue

            try:
                content = full_path.read_text(encoding="utf-8")
                intents = extract_groovy_intent(content)
                resolved[script_path] = intents or ["NO_DETECTABLE_INTENT"]

            except Exception:
                resolved[script_path] = ["FAILED_TO_READ_SCRIPT"]

        return resolved
