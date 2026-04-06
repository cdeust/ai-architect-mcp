"""Heritage (inheritance) data structures.

Provides the HeritageInfo frozen dataclass used by both the
heritage extractor and MRO processor.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HeritageInfo:
    """A single inheritance relationship extracted from source code.

    Args:
        child_id: The graph node ID of the child class.
        parent_name: The name of the parent class or interface.
        heritage_type: Either "extends" or "implements".
        file_path: The source file where the relationship was found.
    """

    child_id: str
    parent_name: str
    heritage_type: str
    file_path: str
