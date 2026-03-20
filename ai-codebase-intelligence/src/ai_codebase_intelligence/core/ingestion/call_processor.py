from __future__ import annotations

import tree_sitter

from ...lib.utils import generate_id
from ..tree_sitter.parser_loader import load_language
from .language_queries import LANGUAGE_QUERIES
from .utils import get_language_from_filename
from ..graph.graph import KnowledgeGraph
from .symbol_table import SymbolTable
from .ast_cache import ASTCache

FUNCTION_NODE_TYPES: frozenset[str] = frozenset({
    "function_declaration", "arrow_function", "function_expression",
    "method_definition", "generator_function_declaration",
    "function_definition", "async_function_declaration",
    "async_arrow_function", "method_declaration",
    "constructor_declaration", "local_function_statement",
    "function_item", "impl_item", "anonymous_function",
    "lambda_literal", "init_declaration", "deinit_declaration",
})

BUILT_IN_NAMES: frozenset[str] = frozenset({
    "console", "log", "warn", "error", "info", "debug",
    "setTimeout", "setInterval", "clearTimeout", "clearInterval",
    "parseInt", "parseFloat", "isNaN", "isFinite",
    "encodeURI", "decodeURI", "encodeURIComponent", "decodeURIComponent",
    "JSON", "parse", "stringify",
    "Object", "Array", "String", "Number", "Boolean", "Symbol", "BigInt",
    "Map", "Set", "WeakMap", "WeakSet",
    "Promise", "resolve", "reject", "then", "catch", "finally",
    "Math", "Date", "RegExp", "Error",
    "require", "import", "export", "fetch", "Response", "Request",
    "useState", "useEffect", "useCallback", "useMemo", "useRef",
    "useContext", "useReducer", "useLayoutEffect",
    "createElement", "createContext", "createRef", "forwardRef", "memo", "lazy",
    "map", "filter", "reduce", "forEach", "find", "findIndex", "some", "every",
    "includes", "indexOf", "slice", "splice", "concat", "join", "split",
    "push", "pop", "shift", "unshift", "sort", "reverse",
    "keys", "values", "entries", "assign", "freeze", "seal",
    "hasOwnProperty", "toString", "valueOf",
    "print", "len", "range", "str", "int", "float", "list", "dict", "set", "tuple",
    "open", "read", "write", "close", "append", "extend", "update",
    "super", "type", "isinstance", "issubclass", "getattr", "setattr", "hasattr",
    "enumerate", "zip", "sorted", "reversed", "min", "max", "sum", "abs",
    "println", "readLine", "require", "requireNotNull", "check", "assert",
    "listOf", "mapOf", "setOf", "mutableListOf", "mutableMapOf", "mutableSetOf",
    "arrayOf", "also", "apply", "run", "with", "takeIf", "takeUnless",
    "TODO", "buildString", "buildList", "repeat", "synchronized",
    "launch", "async", "runBlocking", "withContext", "coroutineScope", "delay",
    "flow", "flowOf", "collect", "emit", "onEach",
    "to", "until", "downTo", "step",
    "printf", "fprintf", "sprintf", "snprintf", "scanf", "fscanf", "sscanf",
    "malloc", "calloc", "realloc", "free", "memcpy", "memmove", "memset",
    "strlen", "strcpy", "strncpy", "strcat", "strcmp", "strncmp", "strstr",
    "atoi", "atol", "atof", "strtol", "sizeof", "offsetof",
    "assert", "abort", "exit", "fopen", "fclose", "fread", "fwrite",
    "printk", "pr_info", "pr_warn", "pr_err", "pr_debug",
    "kfree", "kmalloc", "kzalloc",
    "debugPrint", "dump", "fatalError", "precondition", "NSLog",
    "swap", "MemoryLayout", "compactMap", "flatMap", "contains",
    "first", "last", "prefix", "suffix", "dropFirst", "dropLast",
    "joined", "isEmpty", "count", "index", "startIndex", "endIndex",
    "addSubview", "removeFromSuperview", "layoutSubviews",
    "setNeedsLayout", "layoutIfNeeded", "setNeedsDisplay",
    "addTarget", "removeTarget", "addGestureRecognizer",
    "NSLocalizedString", "Bundle", "reloadData",
    "register", "dequeueReusableCell",
    "present", "dismiss", "pushViewController", "popViewController",
    "performSegue", "prepare",
    "DispatchQueue", "Task", "sink", "store", "receive", "subscribe",
    "addObserver", "removeObserver", "post", "NotificationCenter",
    "get", "put",
})


def _find_enclosing_function(
    node: object, file_path: str, symbol_table: SymbolTable
) -> str | None:
    current = getattr(node, "parent", None)
    while current is not None:
        if current.type in FUNCTION_NODE_TYPES:
            if current.type in ("init_declaration", "deinit_declaration"):
                func_name = "init" if current.type == "init_declaration" else "deinit"
                start_line = current.start_point[0] if hasattr(current, "start_point") else 0
                return generate_id("Constructor", f"{file_path}:{func_name}:{start_line}")

            func_name = None
            label = "Function"

            if current.type in ("function_declaration", "function_definition",
                                "async_function_declaration",
                                "generator_function_declaration", "function_item"):
                name_node = current.child_by_field_name("name")
                if name_node is None:
                    for c in current.named_children:
                        if c.type in ("identifier", "property_identifier", "simple_identifier"):
                            name_node = c
                            break
                func_name = name_node.text.decode("utf-8") if name_node and name_node.text else None

            elif current.type == "method_definition":
                name_node = current.child_by_field_name("name")
                if name_node is None:
                    for c in current.named_children:
                        if c.type == "property_identifier":
                            name_node = c
                            break
                func_name = name_node.text.decode("utf-8") if name_node and name_node.text else None
                label = "Method"

            elif current.type in ("method_declaration", "constructor_declaration"):
                name_node = current.child_by_field_name("name")
                if name_node is None:
                    for c in current.named_children:
                        if c.type == "identifier":
                            name_node = c
                            break
                func_name = name_node.text.decode("utf-8") if name_node and name_node.text else None
                label = "Method"

            elif current.type in ("arrow_function", "function_expression"):
                parent = getattr(current, "parent", None)
                if parent is not None and parent.type == "variable_declarator":
                    name_node = parent.child_by_field_name("name")
                    if name_node is None:
                        for c in parent.named_children:
                            if c.type == "identifier":
                                name_node = c
                                break
                    func_name = name_node.text.decode("utf-8") if name_node and name_node.text else None

            if func_name:
                node_id = symbol_table.lookup_exact(file_path, func_name)
                if node_id:
                    return node_id
                start_line = current.start_point[0] if hasattr(current, "start_point") else 0
                return generate_id(label, f"{file_path}:{func_name}:{start_line}")

        current = getattr(current, "parent", None)
    return None


def _resolve_call_target(
    called_name: str,
    current_file: str,
    symbol_table: SymbolTable,
    import_map: dict[str, set[str]],
) -> dict[str, object] | None:
    local_node_id = symbol_table.lookup_exact(current_file, called_name)
    if local_node_id:
        return {"nodeId": local_node_id, "confidence": 0.85, "reason": "same-file"}

    all_defs = symbol_table.lookup_fuzzy(called_name)
    if all_defs:
        imported_files = import_map.get(current_file)
        if imported_files:
            for d in all_defs:
                if d["filePath"] in imported_files:
                    return {"nodeId": d["nodeId"], "confidence": 0.9, "reason": "import-resolved"}
        confidence = 0.5 if len(all_defs) == 1 else 0.3
        return {"nodeId": all_defs[0]["nodeId"], "confidence": confidence, "reason": "fuzzy-global"}
    return None
