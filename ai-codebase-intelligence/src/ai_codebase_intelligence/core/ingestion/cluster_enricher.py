"""Cluster enricher — 1:1 port of gitnexus cluster-enricher.js."""
from __future__ import annotations

import json
import re
from typing import Any, Callable


def _build_enrichment_prompt(members: list[dict[str, str]], heuristic_label: str) -> str:
    limited = members[:20]
    member_list = ", ".join(f"{m['name']} ({m['type']})" for m in limited)
    extra = f" (+{len(members) - 20} more)" if len(members) > 20 else ""
    return (
        f'Analyze this code cluster and provide a semantic name and short description.\n\n'
        f'Heuristic: "{heuristic_label}"\n'
        f'Members: {member_list}{extra}\n\n'
        f'Reply with JSON only:\n'
        f'{{"name": "2-4 word semantic name", "description": "One sentence describing purpose"}}'
    )


def _parse_enrichment_response(response: str, fallback_label: str) -> dict[str, Any]:
    try:
        m = re.search(r"\{[\s\S]*\}", response)
        if not m:
            raise ValueError("No JSON found")
        parsed = json.loads(m.group(0))
        return {
            "name": parsed.get("name", fallback_label),
            "keywords": parsed.get("keywords", []) if isinstance(parsed.get("keywords"), list) else [],
            "description": parsed.get("description", ""),
        }
    except (json.JSONDecodeError, ValueError):
        return {"name": fallback_label, "keywords": [], "description": ""}


async def enrich_clusters(
    communities: list[dict[str, Any]],
    member_map: dict[str, list[dict[str, str]]],
    llm_client: Any,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    enrichments: dict[str, dict[str, Any]] = {}
    tokens_used = 0

    for i, community in enumerate(communities):
        members = member_map.get(community["id"], [])
        if on_progress:
            on_progress(i + 1, len(communities))

        if not members:
            enrichments[community["id"]] = {
                "name": community["heuristicLabel"],
                "keywords": [],
                "description": "",
            }
            continue

        try:
            prompt = _build_enrichment_prompt(members, community["heuristicLabel"])
            response = await llm_client.generate(prompt)
            tokens_used += len(prompt) // 4 + len(response) // 4
            enrichment = _parse_enrichment_response(response, community["heuristicLabel"])
            enrichments[community["id"]] = enrichment
        except Exception:
            enrichments[community["id"]] = {
                "name": community["heuristicLabel"],
                "keywords": [],
                "description": "",
            }

    return {"enrichments": enrichments, "tokensUsed": tokens_used}


async def enrich_clusters_batch(
    communities: list[dict[str, Any]],
    member_map: dict[str, list[dict[str, str]]],
    llm_client: Any,
    batch_size: int = 5,
    on_progress: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    enrichments: dict[str, dict[str, Any]] = {}
    tokens_used = 0

    for i in range(0, len(communities), batch_size):
        if on_progress:
            on_progress(min(i + batch_size, len(communities)), len(communities))

        batch = communities[i:i + batch_size]
        batch_parts: list[str] = []
        for idx, community in enumerate(batch):
            members = member_map.get(community["id"], [])
            limited = members[:15]
            member_list = ", ".join(f"{m['name']} ({m['type']})" for m in limited)
            batch_parts.append(
                f"Cluster {idx + 1} (id: {community['id']}):\n"
                f'Heuristic: "{community["heuristicLabel"]}"\n'
                f"Members: {member_list}"
            )

        prompt = (
            "Analyze these code clusters and generate semantic names, keywords, and descriptions.\n\n"
            + "\n\n".join(batch_parts)
            + "\n\nOutput JSON array:\n"
            '[\n  {"id": "comm_X", "name": "...", "keywords": [...], "description": "..."},\n  ...\n]'
        )

        try:
            response = await llm_client.generate(prompt)
            tokens_used += len(prompt) // 4 + len(response) // 4
            m = re.search(r"\[[\s\S]*\]", response)
            if m:
                parsed = json.loads(m.group(0))
                for item in parsed:
                    enrichments[item["id"]] = {
                        "name": item.get("name", ""),
                        "keywords": item.get("keywords", []),
                        "description": item.get("description", ""),
                    }
        except Exception:
            for community in batch:
                enrichments[community["id"]] = {
                    "name": community["heuristicLabel"],
                    "keywords": [],
                    "description": "",
                }

    for community in communities:
        if community["id"] not in enrichments:
            enrichments[community["id"]] = {
                "name": community["heuristicLabel"],
                "keywords": [],
                "description": "",
            }

    return {"enrichments": enrichments, "tokensUsed": tokens_used}
