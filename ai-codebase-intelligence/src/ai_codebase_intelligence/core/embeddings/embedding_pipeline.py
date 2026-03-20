"""Embedding pipeline — 1:1 port of gitnexus core/embeddings/embedding-pipeline.js."""
from __future__ import annotations

import logging
from typing import Any, Callable

from .embedder import init_embedder, embed_batch, embed_text, embedding_to_array, is_embedder_ready
from .text_generator import generate_batch_embedding_texts
from .types import DEFAULT_EMBEDDING_CONFIG, EMBEDDABLE_LABELS

logger = logging.getLogger(__name__)


def _query_embeddable_nodes(execute_query: Callable[[str], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    all_nodes: list[dict[str, Any]] = []
    for label in EMBEDDABLE_LABELS:
        try:
            if label == "File":
                query = f"MATCH (n:File) RETURN n.id AS id, n.name AS name, 'File' AS label, n.filePath AS filePath, n.content AS content"
            else:
                query = f"MATCH (n:{label}) RETURN n.id AS id, n.name AS name, '{label}' AS label, n.filePath AS filePath, n.content AS content, n.startLine AS startLine, n.endLine AS endLine"
            rows = execute_query(query)
            for row in rows:
                all_nodes.append({
                    "id": row.get("id", ""), "name": row.get("name", ""),
                    "label": row.get("label", label), "filePath": row.get("filePath", ""),
                    "content": row.get("content", ""),
                    "startLine": row.get("startLine"), "endLine": row.get("endLine"),
                })
        except Exception:
            pass
    return all_nodes


def run_embedding_pipeline(
    execute_query: Callable[[str], list[dict[str, Any]]],
    on_progress: Callable[[dict[str, Any]], None] | None = None,
    config: dict[str, Any] | None = None,
    skip_node_ids: set[str] | None = None,
) -> None:
    cfg = {**DEFAULT_EMBEDDING_CONFIG, **(config or {})}
    progress = on_progress or (lambda d: None)

    progress({"phase": "loading-model", "percent": 0})
    init_embedder(cfg)
    progress({"phase": "loading-model", "percent": 20})

    nodes = _query_embeddable_nodes(execute_query)
    if skip_node_ids:
        nodes = [n for n in nodes if n["id"] not in skip_node_ids]

    total = len(nodes)
    if total == 0:
        progress({"phase": "ready", "percent": 100, "nodesProcessed": 0, "totalNodes": 0})
        return

    batch_size = int(cfg.get("batchSize", 16))
    total_batches = (total + batch_size - 1) // batch_size
    processed = 0

    progress({"phase": "embedding", "percent": 20, "nodesProcessed": 0, "totalNodes": total})

    embedding_updates: list[dict[str, Any]] = []

    for batch_idx in range(total_batches):
        start = batch_idx * batch_size
        end = min(start + batch_size, total)
        batch = nodes[start:end]

        texts = generate_batch_embedding_texts(batch, cfg)
        embeddings = embed_batch(texts)

        for i, node in enumerate(batch):
            embedding_updates.append({"id": node["id"], "embedding": embedding_to_array(embeddings[i])})

        processed += len(batch)
        pct = 20 + int((processed / total) * 70)
        progress({"phase": "embedding", "percent": pct, "nodesProcessed": processed, "totalNodes": total})

    # Store embeddings
    for update in embedding_updates:
        eid = update["id"].replace("'", "''")
        vec_str = str(update["embedding"])
        try:
            execute_query(f"CREATE (:CodeEmbedding {{nodeId: '{eid}', embedding: {vec_str}}})")
        except Exception:
            pass

    # Create vector index
    progress({"phase": "indexing", "percent": 90})
    try:
        execute_query("CALL CREATE_VECTOR_INDEX('CodeEmbedding', 'code_embedding_idx', 'embedding', metric := 'cosine')")
    except Exception:
        pass

    progress({"phase": "ready", "percent": 100, "nodesProcessed": total, "totalNodes": total})


def semantic_search(
    execute_query: Callable[[str], list[dict[str, Any]]],
    query: str,
    k: int = 10,
    max_distance: float = 0.5,
) -> list[dict[str, Any]]:
    if not is_embedder_ready():
        return []

    query_embedding = embed_text(query)
    query_vec = embedding_to_array(query_embedding)
    query_vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

    vector_query = (
        f"CALL QUERY_VECTOR_INDEX('CodeEmbedding', 'code_embedding_idx', "
        f"CAST({query_vec_str} AS FLOAT[384]), {k}) "
        f"YIELD node AS emb, distance "
        f"WITH emb, distance WHERE distance < {max_distance} "
        f"RETURN emb.nodeId AS nodeId, distance ORDER BY distance"
    )

    try:
        emb_results = execute_query(vector_query)
    except Exception:
        return []

    results: list[dict[str, Any]] = []
    for row in emb_results:
        node_id = row.get("nodeId", "")
        distance = row.get("distance", 0)
        colon = node_id.find(":")
        label = node_id[:colon] if colon > 0 else "Unknown"

        try:
            esc_id = node_id.replace("'", "''")
            if label == "File":
                nq = f"MATCH (n:File {{id: '{esc_id}'}}) RETURN n.name AS name, n.filePath AS filePath"
            else:
                nq = f"MATCH (n:`{label}` {{id: '{esc_id}'}}) RETURN n.name AS name, n.filePath AS filePath, n.startLine AS startLine, n.endLine AS endLine"
            node_rows = execute_query(nq)
            if node_rows:
                nr = node_rows[0]
                results.append({
                    "nodeId": node_id, "name": nr.get("name", ""),
                    "label": label, "filePath": nr.get("filePath", ""),
                    "distance": distance,
                    "startLine": nr.get("startLine") if label != "File" else None,
                    "endLine": nr.get("endLine") if label != "File" else None,
                })
        except Exception:
            pass

    return results
