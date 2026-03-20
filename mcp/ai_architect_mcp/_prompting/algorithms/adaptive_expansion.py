"""Adaptive Expansion — Tree/Graph of Thoughts hybrid exploration.

Research: Yao et al. (2023) ToT; Besta et al. (2023) GoT; ETH Zurich AGoT 2025.
"""

from __future__ import annotations

from uuid import uuid4

from ai_architect_mcp._models.graph import ThoughtEdge, ThoughtGraph, ThoughtNode
from ai_architect_mcp._models.prompting import EnhancedPrompt

DEFAULT_MAX_DEPTH = 10
DEFAULT_EXPANSION_THRESHOLD = 0.5
DEFAULT_MIN_NODES_BEFORE_PRUNING = 3


class AdaptiveExpansion:
    """Adaptive expansion with Tree/Graph of Thoughts."""

    def __init__(self, client: object | None = None) -> None:
        self._client = client

    async def expand(
        self,
        prompt: str,
        context: str,
        max_depth: int = DEFAULT_MAX_DEPTH,
        expansion_threshold: float = DEFAULT_EXPANSION_THRESHOLD,
        min_nodes_before_pruning: int = DEFAULT_MIN_NODES_BEFORE_PRUNING,
    ) -> EnhancedPrompt:
        """Expand a prompt through thought graph exploration.

        Args:
            prompt: The original prompt.
            context: Supporting context.
            max_depth: Maximum exploration depth.
            expansion_threshold: Minimum confidence to continue expanding.
            min_nodes_before_pruning: Minimum nodes before pruning starts.

        Returns:
            EnhancedPrompt with graph-enhanced version.
        """
        root_id = uuid4()
        root = ThoughtNode(node_id=root_id, content=prompt, confidence=0.8, depth=0)
        nodes: list[ThoughtNode] = [root]
        edges: list[ThoughtEdge] = []

        iterations = await self._explore_graph(
            nodes, edges, context, max_depth,
            expansion_threshold, min_nodes_before_pruning,
        )

        return self._assemble_result(prompt, nodes, edges, root_id, iterations)

    async def _explore_graph(
        self,
        nodes: list[ThoughtNode],
        edges: list[ThoughtEdge],
        context: str,
        max_depth: int,
        threshold: float,
        min_prune: int,
    ) -> int:
        """Run the expansion loop, mutating nodes/edges in place.

        Returns:
            Number of iterations performed.
        """
        current_depth = 0
        iterations = 0

        while current_depth < max_depth:
            iterations += 1
            leaves = [
                n for n in nodes
                if n.depth == current_depth and n.confidence >= threshold
            ]
            if not leaves:
                break

            added = await self._expand_leaves(
                leaves, nodes, edges, context, threshold, current_depth,
            )
            if not added:
                break

            if len(nodes) >= min_prune:
                pruned_n, pruned_e = self._prune(nodes, edges, threshold * 0.8)
                nodes.clear()
                nodes.extend(pruned_n)
                edges.clear()
                edges.extend(pruned_e)

            current_depth += 1

        return iterations

    async def _expand_leaves(
        self,
        leaves: list[ThoughtNode],
        nodes: list[ThoughtNode],
        edges: list[ThoughtEdge],
        context: str,
        threshold: float,
        depth: int,
    ) -> bool:
        """Expand all leaf nodes, appending children to nodes/edges.

        Returns:
            True if at least one child was added.
        """
        added = False
        for leaf in leaves:
            content = await self._generate_expansion(leaf.content, context)
            confidence = await self._evaluate_node(content, context)

            if confidence >= threshold:
                child = ThoughtNode(
                    node_id=uuid4(), content=content,
                    confidence=round(confidence, 4), depth=depth + 1,
                )
                nodes.append(child)
                edges.append(ThoughtEdge(
                    source_id=leaf.node_id, target_id=child.node_id,
                    relationship="expansion", weight=round(confidence, 4),
                ))
                added = True
        return added

    def _assemble_result(
        self,
        prompt: str,
        nodes: list[ThoughtNode],
        edges: list[ThoughtEdge],
        root_id: object,
        iterations: int,
    ) -> EnhancedPrompt:
        """Build the final EnhancedPrompt from explored graph."""
        graph = ThoughtGraph(nodes=nodes, edges=edges, root_id=root_id)
        best_path = self._extract_best_path(graph)
        enhanced = self._synthesize(prompt, best_path)
        avg_confidence = sum(n.confidence for n in nodes) / max(len(nodes), 1)

        return EnhancedPrompt(
            original=prompt, enhanced=enhanced,
            strategy_used="adaptive_expansion",
            confidence=round(min(1.0, avg_confidence), 4),
            iterations=iterations,
        )

    async def _generate_expansion(self, content: str, context: str) -> str:
        """Generate an expansion of a thought node.

        Args:
            content: The thought content to expand.
            context: Supporting context.

        Returns:
            Expanded thought content.
        """
        if self._client is None:
            return f"Expanded: {content[:100]}... considering {context[:50]}"
        return content

    async def _evaluate_node(self, content: str, context: str) -> float:
        """Evaluate confidence in a thought node.

        Args:
            content: The thought content to evaluate.
            context: Supporting context.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        if self._client is None:
            return min(0.9, 0.6 + len(content) * 0.001)
        return 0.7

    def _prune(
        self, nodes: list[ThoughtNode], edges: list[ThoughtEdge], threshold: float
    ) -> tuple[list[ThoughtNode], list[ThoughtEdge]]:
        """Remove low-confidence nodes.

        Args:
            nodes: All nodes in the graph.
            edges: All edges in the graph.
            threshold: Minimum confidence to keep a node.

        Returns:
            Tuple of pruned nodes and edges.
        """
        keep_ids = {
            n.node_id for n in nodes
            if n.confidence >= threshold or n.depth == 0
        }
        pruned_nodes = [n for n in nodes if n.node_id in keep_ids]
        pruned_edges = [
            e for e in edges
            if e.source_id in keep_ids and e.target_id in keep_ids
        ]
        return pruned_nodes, pruned_edges

    def _extract_best_path(self, graph: ThoughtGraph) -> list[ThoughtNode]:
        """Extract the highest-confidence path from root to deepest node.

        Args:
            graph: The thought graph to extract from.

        Returns:
            List of nodes forming the best path.
        """
        if not graph.nodes:
            return []
        nodes_by_id = {n.node_id: n for n in graph.nodes}
        children: dict[str, list[ThoughtNode]] = {}
        for edge in graph.edges:
            src = str(edge.source_id)
            target_node = nodes_by_id.get(edge.target_id)
            if target_node is not None:
                children.setdefault(src, []).append(target_node)

        path: list[ThoughtNode] = [nodes_by_id[graph.root_id]]
        current = graph.root_id
        while str(current) in children:
            child_list = children[str(current)]
            best = max(child_list, key=lambda n: n.confidence)
            path.append(best)
            current = best.node_id
        return path

    def _synthesize(self, original: str, path: list[ThoughtNode]) -> str:
        """Synthesize enhanced prompt from best path.

        Args:
            original: The original prompt.
            path: The best thought path.

        Returns:
            Synthesized enhanced prompt.
        """
        if len(path) <= 1:
            return original
        insights = [n.content for n in path[1:]]
        return f"{original}\n\nInsights from exploration:\n" + "\n".join(
            f"- {i}" for i in insights
        )
