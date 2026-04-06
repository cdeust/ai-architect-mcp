from __future__ import annotations

from .ignore_service import (
    DEFAULT_IGNORE_DIRS,
    IGNORED_EXTENSIONS,
    IGNORED_FILES,
    MAX_FILE_SIZE_BYTES,
    should_ignore_dir,
    should_ignore_file,
)
from .supported_languages import (
    GRAMMAR_NAMES,
    LANGUAGE_EXTENSIONS,
    SupportedLanguage,
    detect_language,
    get_grammar_name,
)
