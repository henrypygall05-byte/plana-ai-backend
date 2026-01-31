"""
Prompt loader for versioned prompts.

Loads prompts from the prompts directory with version tracking.
"""

import json
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass

# Default versions
DEFAULT_PROMPT_VERSION = "1.0.0"
DEFAULT_SCHEMA_VERSION = "1.0.0"


@dataclass
class PromptInfo:
    """Information about a loaded prompt."""

    name: str
    version: str
    content: str
    schema_version: str
    path: Path


class PromptLoader:
    """
    Loads and manages versioned prompts.

    Prompts are stored in /prompts/v{version}/ directory.
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        """Initialize the prompt loader.

        Args:
            prompts_dir: Root prompts directory. Defaults to project/prompts/
        """
        if prompts_dir is None:
            # Find prompts directory relative to this file
            self.prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)

        self._cache: Dict[str, PromptInfo] = {}

    def get_version_dir(self, version: str) -> Path:
        """Get the directory for a specific prompt version."""
        # Convert version like "1.0.0" to "v1.0"
        major_minor = ".".join(version.split(".")[:2])
        return self.prompts_dir / f"v{major_minor}"

    def load_prompt(self, name: str, version: str = DEFAULT_PROMPT_VERSION) -> PromptInfo:
        """Load a prompt by name and version.

        Args:
            name: Prompt name (e.g., "case_officer", "evaluator")
            version: Prompt version (e.g., "1.0.0")

        Returns:
            PromptInfo with content and metadata
        """
        cache_key = f"{name}:{version}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        version_dir = self.get_version_dir(version)
        prompt_path = version_dir / f"{name}.md"

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")

        content = prompt_path.read_text(encoding="utf-8")

        info = PromptInfo(
            name=name,
            version=version,
            content=content,
            schema_version=DEFAULT_SCHEMA_VERSION,
            path=prompt_path,
        )

        self._cache[cache_key] = info
        return info

    def load_schema(self, name: str, version: str = DEFAULT_SCHEMA_VERSION) -> Dict[str, Any]:
        """Load a JSON schema by name and version.

        Args:
            name: Schema name (e.g., "case_input", "case_output")
            version: Schema version

        Returns:
            Parsed JSON schema
        """
        version_dir = self.get_version_dir(version)
        schema_path = version_dir / "schemas" / f"{name}.json"

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")

        return json.loads(schema_path.read_text(encoding="utf-8"))

    def get_available_versions(self) -> list:
        """Get list of available prompt versions."""
        versions = []
        if self.prompts_dir.exists():
            for item in self.prompts_dir.iterdir():
                if item.is_dir() and item.name.startswith("v"):
                    versions.append(item.name[1:] + ".0")  # v1.0 -> 1.0.0
        return sorted(versions)


# Module-level loader instance
_loader: Optional[PromptLoader] = None


def get_loader() -> PromptLoader:
    """Get the singleton prompt loader."""
    global _loader
    if _loader is None:
        _loader = PromptLoader()
    return _loader


def get_case_officer_prompt(version: str = DEFAULT_PROMPT_VERSION) -> PromptInfo:
    """Get the Case Officer prompt.

    Args:
        version: Prompt version (default: 1.0.0)

    Returns:
        PromptInfo with case officer prompt content
    """
    return get_loader().load_prompt("case_officer", version)


def get_evaluator_prompt(version: str = DEFAULT_PROMPT_VERSION) -> PromptInfo:
    """Get the Evaluator prompt for QC.

    Args:
        version: Prompt version (default: 1.0.0)

    Returns:
        PromptInfo with evaluator prompt content
    """
    return get_loader().load_prompt("evaluator", version)


def get_case_input_schema(version: str = DEFAULT_SCHEMA_VERSION) -> Dict[str, Any]:
    """Get the CASE_INPUT JSON schema.

    Args:
        version: Schema version

    Returns:
        JSON schema as dict
    """
    return get_loader().load_schema("case_input", version)


def get_case_output_schema(version: str = DEFAULT_SCHEMA_VERSION) -> Dict[str, Any]:
    """Get the CASE_OUTPUT JSON schema.

    Args:
        version: Schema version

    Returns:
        JSON schema as dict
    """
    return get_loader().load_schema("case_output", version)
