"""NLI Entailment Evaluator — classify claims via natural language inference.

Classifies: ENTAILMENT (1.0), NEUTRAL (0.3-0.6), CONTRADICTION (0.0).
Research: Bowman et al. (2015) SNLI; Williams et al. (2018) MultiNLI.
"""

from __future__ import annotations

from ai_architect_mcp._models.verification import (
    ClaimEvaluation,
    Verdict,
    VerificationClaim,
)

ENTAILMENT_SCORE = 1.0
NEUTRAL_STRICT_SCORE = 0.3
NEUTRAL_LENIENT_SCORE = 0.6
CONTRADICTION_SCORE = 0.0
TEMPERATURE = 0.1
NLI_CONFIDENCE = 0.85
PREMISE_PREVIEW_LEN = 200
DEFAULT_MODEL = "claude-sonnet-4-20250514"

NLI_PROMPT_TEMPLATE = (
    "Classify the relationship between the premise and hypothesis.\n\n"
    "Premise: {premise}\n"
    "Hypothesis: {hypothesis}\n\n"
    "Classification (respond with exactly one):\n"
    "- ENTAILMENT: The premise logically implies the hypothesis\n"
    "- NEUTRAL: The premise neither supports nor contradicts\n"
    "- CONTRADICTION: The premise contradicts the hypothesis\n\n"
    "Classification:"
)


class NLIEntailmentEvaluator:
    """NLI-based claim evaluator using natural language inference.

    Uses an LLM to classify the entailment relationship between
    a claim and its supporting premise/context.
    """

    def __init__(
        self,
        client: object,
        strict: bool = True,
        model: str = DEFAULT_MODEL,
    ) -> None:
        """Initialize the NLI evaluator.

        Args:
            client: Anthropic client for LLM calls.
            strict: If True, NEUTRAL scores 0.3. If False, 0.6.
            model: Model ID for LLM calls.
        """
        if client is None:
            raise ValueError(
                "NLIEntailmentEvaluator requires an LLM client. "
                "Provide a Claude CLI client or AsyncAnthropic instance."
            )
        self._client = client
        self._strict = strict
        self._model = model

    async def evaluate(
        self, claim: VerificationClaim, premise: str
    ) -> ClaimEvaluation:
        """Evaluate a claim against a premise using NLI.

        Args:
            claim: The claim to evaluate.
            premise: The context/premise to evaluate against.

        Returns:
            ClaimEvaluation with NLI-based score and verdict.
        """
        classification = await self._classify(claim.content, premise)
        score, verdict = self._map_classification(classification)

        return ClaimEvaluation(
            claim_id=claim.claim_id,
            evaluator_id="nli_entailment",
            score=score,
            confidence=NLI_CONFIDENCE,
            verdict=verdict,
            reasoning=f"NLI classification: {classification}",
            evidence=[premise[:PREMISE_PREVIEW_LEN]],
        )

    async def evaluate_batch(
        self, claims: list[VerificationClaim], premise: str
    ) -> list[ClaimEvaluation]:
        """Evaluate multiple claims against the same premise.

        Args:
            claims: Claims to evaluate.
            premise: Shared context/premise.

        Returns:
            List of ClaimEvaluation results.
        """
        results: list[ClaimEvaluation] = []
        for claim in claims:
            result = await self.evaluate(claim, premise)
            results.append(result)
        return results

    def _map_classification(
        self, classification: str
    ) -> tuple[float, Verdict]:
        """Map NLI classification to score and verdict.

        Args:
            classification: One of ENTAILMENT, NEUTRAL, CONTRADICTION.

        Returns:
            Tuple of (score, verdict).
        """
        if classification == "ENTAILMENT":
            return ENTAILMENT_SCORE, Verdict.PASS
        if classification == "CONTRADICTION":
            return CONTRADICTION_SCORE, Verdict.FAIL
        neutral_score = (
            NEUTRAL_STRICT_SCORE if self._strict else NEUTRAL_LENIENT_SCORE
        )
        return neutral_score, Verdict.INCONCLUSIVE

    async def _classify(
        self, hypothesis: str, premise: str
    ) -> str:
        """Classify the NLI relationship using LLM.

        Args:
            hypothesis: The hypothesis (claim text).
            premise: The premise (context).

        Returns:
            Classification string: ENTAILMENT, NEUTRAL, or CONTRADICTION.
        """
        prompt = NLI_PROMPT_TEMPLATE.format(
            premise=premise, hypothesis=hypothesis
        )

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=50,
                temperature=TEMPERATURE,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip().upper()
            if "ENTAILMENT" in text:
                return "ENTAILMENT"
            if "CONTRADICTION" in text:
                return "CONTRADICTION"
            return "NEUTRAL"
        except (AttributeError, IndexError, TypeError):
            return "NEUTRAL"
