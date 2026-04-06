"""KuzuDB Schema."""
from __future__ import annotations

NODE_TABLES = [
    "File", "Folder", "Function", "Class", "Interface", "Method", "CodeElement",
    "Community", "Process", "Contributor",
    "Struct", "Enum", "Macro", "Typedef", "Union", "Namespace", "Trait", "Impl",
    "TypeAlias", "Const", "Static", "Property", "Record", "Delegate", "Annotation",
    "Constructor", "Template", "Module",
]

REL_TABLE_NAME = "CodeRelation"
REL_TYPES = [
    "CONTAINS", "DEFINES", "IMPORTS", "CALLS", "EXTENDS", "IMPLEMENTS",
    "MEMBER_OF", "STEP_IN_PROCESS", "AUTHORED_BY", "CO_CHANGES_WITH",
]
EMBEDDING_TABLE_NAME = "CodeEmbedding"

FILE_SCHEMA = "CREATE NODE TABLE File (id STRING, name STRING, filePath STRING, content STRING, PRIMARY KEY (id))"
FOLDER_SCHEMA = "CREATE NODE TABLE Folder (id STRING, name STRING, filePath STRING, PRIMARY KEY (id))"

_SYM_EXP = "(id STRING, name STRING, filePath STRING, startLine INT64, endLine INT64, isExported BOOLEAN, content STRING, description STRING, PRIMARY KEY (id))"
_SYM_BASE = "(id STRING, name STRING, filePath STRING, startLine INT64, endLine INT64, content STRING, description STRING, PRIMARY KEY (id))"

FUNCTION_SCHEMA = f"CREATE NODE TABLE Function {_SYM_EXP}"
CLASS_SCHEMA = f"CREATE NODE TABLE Class {_SYM_EXP}"
INTERFACE_SCHEMA = f"CREATE NODE TABLE Interface {_SYM_EXP}"
METHOD_SCHEMA = f"CREATE NODE TABLE Method {_SYM_EXP}"
CODE_ELEMENT_SCHEMA = f"CREATE NODE TABLE CodeElement {_SYM_EXP}"

COMMUNITY_SCHEMA = "CREATE NODE TABLE Community (id STRING, label STRING, heuristicLabel STRING, keywords STRING[], description STRING, enrichedBy STRING, cohesion DOUBLE, symbolCount INT32, PRIMARY KEY (id))"
PROCESS_SCHEMA = "CREATE NODE TABLE Process (id STRING, label STRING, heuristicLabel STRING, processType STRING, stepCount INT32, communities STRING[], entryPointId STRING, terminalId STRING, PRIMARY KEY (id))"
CONTRIBUTOR_SCHEMA = "CREATE NODE TABLE Contributor (id STRING, name STRING, email STRING, commitCount INT32, PRIMARY KEY (id))"

def _ml(n: str) -> str:
    return f"CREATE NODE TABLE IF NOT EXISTS {n} {_SYM_BASE}"

EMBEDDING_SCHEMA = f"CREATE NODE TABLE {EMBEDDING_TABLE_NAME} (nodeId STRING, embedding FLOAT[384], PRIMARY KEY (nodeId))"

NODE_SCHEMA_QUERIES = [
    FILE_SCHEMA, FOLDER_SCHEMA, FUNCTION_SCHEMA, CLASS_SCHEMA, INTERFACE_SCHEMA,
    METHOD_SCHEMA, CODE_ELEMENT_SCHEMA, COMMUNITY_SCHEMA, PROCESS_SCHEMA, CONTRIBUTOR_SCHEMA,
    _ml("Struct"), _ml("Enum"), _ml("Macro"), _ml("Typedef"), _ml("Union"),
    _ml("Namespace"), _ml("Trait"), _ml("Impl"), _ml("TypeAlias"), _ml("Const"),
    _ml("Static"), _ml("Property"), _ml("Record"), _ml("Delegate"),
    _ml("Annotation"), _ml("Constructor"), _ml("Template"), _ml("Module"),
]

# Import the relation schema from separate file (too large for one)
from .schema_rels import RELATION_SCHEMA

REL_SCHEMA_QUERIES = [RELATION_SCHEMA]

SCHEMA_QUERIES = NODE_SCHEMA_QUERIES + REL_SCHEMA_QUERIES + [EMBEDDING_SCHEMA]

FTS_INDEX_SCHEMAS = [
    "CALL CREATE_FTS_INDEX('File', 'file_fts', ['name', 'content'])",
    "CALL CREATE_FTS_INDEX('Function', 'function_fts', ['name', 'content'])",
    "CALL CREATE_FTS_INDEX('Class', 'class_fts', ['name', 'content'])",
    "CALL CREATE_FTS_INDEX('Method', 'method_fts', ['name', 'content'])",
    "CALL CREATE_FTS_INDEX('Interface', 'interface_fts', ['name', 'content'])",
]

CREATE_VECTOR_INDEX_QUERY = f"CALL CREATE_VECTOR_INDEX('{EMBEDDING_TABLE_NAME}', 'code_embedding_idx', 'embedding', metric := 'cosine')"
