"""Import path resolution — suffix index, extension tries, caching."""
from __future__ import annotations

from typing import Any

from ...config.supported_languages import SupportedLanguages

RESOLVE_CACHE_CAP = 100_000

EXTENSIONS: list[str] = [
    "",
    ".tsx", ".ts", ".jsx", ".js", "/index.tsx", "/index.ts", "/index.jsx", "/index.js",
    ".py", "/__init__.py",
    ".java", ".kt", ".kts",
    ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx", ".hxx", ".hh",
    ".cs", ".go", ".rs", "/mod.rs", ".php", ".phtml", ".swift",
]


def build_suffix_index(
    normalized_file_list: list[str], all_file_list: list[str]
) -> dict[str, Any]:
    exact_map: dict[str, str] = {}
    lower_map: dict[str, str] = {}
    dir_map: dict[str, list[str]] = {}

    for i, normalized in enumerate(normalized_file_list):
        original = all_file_list[i]
        parts = normalized.split("/")
        for j in range(len(parts) - 1, -1, -1):
            suffix = "/".join(parts[j:])
            if suffix not in exact_map:
                exact_map[suffix] = original
            low = suffix.lower()
            if low not in lower_map:
                lower_map[low] = original

        last_slash = normalized.rfind("/")
        if last_slash >= 0:
            dir_parts = parts[:-1]
            file_name = parts[-1]
            dot_idx = file_name.rfind(".")
            ext = file_name[dot_idx:] if dot_idx >= 0 else ""
            for j in range(len(dir_parts) - 1, -1, -1):
                dir_suffix = "/".join(dir_parts[j:])
                key = f"{dir_suffix}:{ext}"
                dir_map.setdefault(key, []).append(original)

    return {
        "_exact": exact_map,
        "_lower": lower_map,
        "_dir": dir_map,
    }


def suffix_index_get(index: dict[str, Any], suffix: str) -> str | None:
    return index["_exact"].get(suffix)


def suffix_index_get_insensitive(index: dict[str, Any], suffix: str) -> str | None:
    return index["_lower"].get(suffix.lower())


def suffix_index_get_files_in_dir(
    index: dict[str, Any], dir_suffix: str, extension: str
) -> list[str]:
    return index["_dir"].get(f"{dir_suffix}:{extension}", [])


def try_resolve_with_extensions(base_path: str, all_files: set[str]) -> str | None:
    for ext in EXTENSIONS:
        candidate = base_path + ext
        if candidate in all_files:
            return candidate
    return None


def suffix_resolve(
    path_parts: list[str],
    normalized_file_list: list[str],
    all_file_list: list[str],
    index: dict[str, Any] | None,
) -> str | None:
    if index is not None:
        for i in range(len(path_parts)):
            suffix = "/".join(path_parts[i:])
            for ext in EXTENSIONS:
                suffix_with_ext = suffix + ext
                result = (suffix_index_get(index, suffix_with_ext)
                          or suffix_index_get_insensitive(index, suffix_with_ext))
                if result:
                    return result
        return None

    for i in range(len(path_parts)):
        suffix = "/".join(path_parts[i:])
        for ext in EXTENSIONS:
            suffix_with_ext = suffix + ext
            suffix_pattern = "/" + suffix_with_ext
            for j, fp in enumerate(normalized_file_list):
                if fp.endswith(suffix_pattern) or fp.lower().endswith(suffix_pattern.lower()):
                    return all_file_list[j]
    return None


def resolve_rust_import(
    current_file: str, import_path: str, all_files: set[str]
) -> str | None:
    if import_path.startswith("crate::"):
        rust_path = import_path[7:].replace("::", "/")
        result = _try_rust_module_path("src/" + rust_path, all_files)
        if result:
            return result
        return _try_rust_module_path(rust_path, all_files)

    if import_path.startswith("super::"):
        current_dir = current_file.split("/")[:-1]
        if current_dir:
            current_dir.pop()
        rust_path = import_path[7:].replace("::", "/")
        full = "/".join(current_dir + [rust_path])
        return _try_rust_module_path(full, all_files)

    if import_path.startswith("self::"):
        current_dir = current_file.split("/")[:-1]
        rust_path = import_path[6:].replace("::", "/")
        full = "/".join(current_dir + [rust_path])
        return _try_rust_module_path(full, all_files)

    if "::" in import_path:
        rust_path = import_path.replace("::", "/")
        return _try_rust_module_path(rust_path, all_files)

    return None


def _try_rust_module_path(module_path: str, all_files: set[str]) -> str | None:
    if module_path + ".rs" in all_files:
        return module_path + ".rs"
    if module_path + "/mod.rs" in all_files:
        return module_path + "/mod.rs"
    if module_path + "/lib.rs" in all_files:
        return module_path + "/lib.rs"
    last_slash = module_path.rfind("/")
    if last_slash > 0:
        parent = module_path[:last_slash]
        if parent + ".rs" in all_files:
            return parent + ".rs"
        if parent + "/mod.rs" in all_files:
            return parent + "/mod.rs"
    return None


def resolve_import_path(
    current_file: str,
    import_path: str,
    all_files: set[str],
    all_file_list: list[str],
    normalized_file_list: list[str],
    resolve_cache: dict[str, str | None],
    language: str,
    tsconfig_paths: dict[str, Any] | None,
    index: dict[str, Any] | None,
) -> str | None:
    cache_key = f"{current_file}::{import_path}"
    if cache_key in resolve_cache:
        return resolve_cache[cache_key]

    def cache(result: str | None) -> str | None:
        if len(resolve_cache) >= RESOLVE_CACHE_CAP:
            evict_count = int(RESOLVE_CACHE_CAP * 0.2)
            keys = list(resolve_cache.keys())[:evict_count]
            for k in keys:
                del resolve_cache[k]
        resolve_cache[cache_key] = result
        return result

    # TypeScript/JavaScript: rewrite path aliases
    if (language in (SupportedLanguages.TypeScript, SupportedLanguages.JavaScript)
            and tsconfig_paths is not None
            and not import_path.startswith(".")):
        for alias_prefix, target_prefix in tsconfig_paths["aliases"].items():
            if import_path.startswith(alias_prefix):
                remainder = import_path[len(alias_prefix):]
                base_url = tsconfig_paths.get("baseUrl", ".")
                rewritten = (target_prefix + remainder if base_url == "."
                             else base_url + "/" + target_prefix + remainder)
                resolved = try_resolve_with_extensions(rewritten, all_files)
                if resolved:
                    return cache(resolved)
                parts = [p for p in rewritten.split("/") if p]
                sr = suffix_resolve(parts, normalized_file_list, all_file_list, index)
                if sr:
                    return cache(sr)

    # Rust: convert module path syntax
    if language == SupportedLanguages.Rust:
        rust_result = resolve_rust_import(current_file, import_path, all_files)
        if rust_result:
            return cache(rust_result)

    # Generic relative import (./ and ../)
    current_dir = current_file.split("/")[:-1]
    for part in import_path.split("/"):
        if part == ".":
            continue
        if part == "..":
            if current_dir:
                current_dir.pop()
        else:
            current_dir.append(part)

    base_path = "/".join(current_dir)
    if import_path.startswith("."):
        resolved = try_resolve_with_extensions(base_path, all_files)
        return cache(resolved)

    # Java wildcards handled elsewhere
    if import_path.endswith(".*"):
        return cache(None)

    path_like = import_path if "/" in import_path else import_path.replace(".", "/")
    path_parts = [p for p in path_like.split("/") if p]
    resolved = suffix_resolve(path_parts, normalized_file_list, all_file_list, index)
    return cache(resolved)


def build_import_resolution_context(
    all_paths: list[str],
) -> dict[str, Any]:
    normalized = [p.replace("\\", "/") for p in all_paths]
    idx = build_suffix_index(normalized, all_paths)
    return {
        "allFilePaths": set(all_paths),
        "allFileList": all_paths,
        "normalizedFileList": normalized,
        "suffixIndex": idx,
        "resolveCache": {},
    }
