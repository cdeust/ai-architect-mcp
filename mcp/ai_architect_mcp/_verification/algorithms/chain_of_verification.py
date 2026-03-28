"""Chain of Verification — reduces hallucination through structured verification.

4-step CoV: generate questions -> answer independently -> evaluate ->
synthesize. Research: Dhuliawala et al. (2023).
"""

from __future__ import annotations

from ai_architect_mcp._models.verification import (
    ClaimEvaluation,
    Verdict,
    VerificationClaim,
)

MIN_QUESTIONS = 5
MAX_QUESTIONS = 15
PASS_THRESHOLD = 0.7
INCONCLUSIVE_THRESHOLD = 0.4
CONFIDENCE_SCALE = 1.1
DEFAULT_MODEL = "claude-sonnet-4-20250514"


class ChainOfVerification:
    """Chain of Verification for claim evaluation.

    Generates verification questions, answers them independently,
    evaluates answer consistency, and synthesizes a final verdict.
    """

    def __init__(self, client: object, model: str = DEFAULT_MODEL) -> None:
        """Initialize Chain of Verification.

        Args:
            client: Anthropic client for LLM calls.
            model: Model ID for LLM calls.
        """
        if client is None:
            raise ValueError(
                "ChainOfVerification requires an LLM client. "
                "Provide a Claude CLI client or AsyncAnthropic instance."
            )
        self._client = client
        self._model = model

    async def verify(
        self, claim: VerificationClaim, context: str
    ) -> ClaimEvaluation:
        """Verify a claim using the 4-step CoV process.

        Args:
            claim: The claim to verify.
            context: Supporting context for verification.

        Returns:
            ClaimEvaluation with CoV-based assessment.
        """
        questions = await self._generate_questions(claim, context)
        answers = await self._answer_independently(questions, context)
        evaluations = await self._evaluate_answers(
            questions, answers, claim
        )
        return self._synthesize_verdict(claim, evaluations)

    async def _generate_questions(
        self, claim: VerificationClaim, context: str
    ) -> list[str]:
        """Generate verification questions for the claim.

        Args:
            claim: The claim to generate questions for.
            context: Supporting context.

        Returns:
            List of verification questions.
        """
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                temperature=0.7,
                system=(
                    "Generate verification questions to check whether a claim "
                    "is accurate. Output one question per line, numbered. "
                    f"Generate between {MIN_QUESTIONS} and {MAX_QUESTIONS} questions."
                ),
                messages=[{
                    "role": "user",
                    "content": (
                        f"Claim: {claim.content}\n\n"
                        f"Context:\n{context}"
                    ),
                }],
            )
            text = response.content[0].text.strip()
            lines = [
                ln.lstrip("0123456789.) ").strip()
                for ln in text.splitlines()
                if ln.strip() and any(c.isalpha() for c in ln)
            ]
            if len(lines) >= MIN_QUESTIONS:
                return lines[:MAX_QUESTIONS]
            return self._fallback_questions(claim)
        except (AttributeError, IndexError, TypeError):
            return self._fallback_questions(claim)
        except Exception:
            return self._fallback_questions(claim)

    async def _answer_independently(
        self, questions: list[str], context: str
    ) -> list[str]:
        """Answer each question independently without seeing other answers.

        Args:
            questions: Verification questions.
            context: Supporting context.

        Returns:
            Independent answers for each question.
        """
        answers: list[str] = []
        for question in questions:
            try:
                response = await self._client.messages.create(
                    model=self._model,
                    max_tokens=512,
                    temperature=0.3,
                    system=(
                        "Answer the verification question using ONLY the provided "
                        "context. Be concise and factual."
                    ),
                    messages=[{
                        "role": "user",
                        "content": (
                            f"Question: {question}\n\n"
                            f"Context:\n{context}"
                        ),
                    }],
                )
                answers.append(response.content[0].text.strip())
            except (AttributeError, IndexError, TypeError):
                answers.append("Unable to evaluate this question.")
            except Exception:
                answers.append("Unable to evaluate this question.")
        return answers

    async def _evaluate_answers(
        self,
        questions: list[str],
        answers: list[str],
        claim: VerificationClaim,
    ) -> list[float]:
        """Evaluate consistency of answers.

        Args:
            questions: Original verification questions.
            answers: Independent answers.
            claim: The claim being verified.

        Returns:
            Consistency scores for each question-answer pair.
        """
        scores: list[float] = []
        for question, answer in zip(questions, answers):
            try:
                response = await self._client.messages.create(
                    model=self._model,
                    max_tokens=50,
                    temperature=0.1,
                    system=(
                        "Rate how well the answer supports the claim on a scale "
                        "of 0.0 to 1.0. Respond with only a number."
                    ),
                    messages=[{
                        "role": "user",
                        "content": (
                            f"Claim: {claim.content}\n"
                            f"Question: {question}\n"
                            f"Answer: {answer}"
                        ),
                    }],
                )
                text = response.content[0].text.strip()
                score = float(text.split()[0].strip(".,;:"))
                scores.append(max(0.0, min(1.0, score)))
            except (AttributeError, IndexError, TypeError, ValueError):
                scores.append(0.5)
            except Exception:
                scores.append(0.5)
        return scores

    def _synthesize_verdict(
        self,
        claim: VerificationClaim,
        evaluations: list[float],
    ) -> ClaimEvaluation:
        """Synthesize final verdict from question evaluations.

        Args:
            claim: The claim being verified.
            evaluations: Scores from question evaluations.

        Returns:
            Final ClaimEvaluation with synthesized verdict.
        """
        if not evaluations:
            score = 0.5
        else:
            score = sum(evaluations) / len(evaluations)

        if score >= PASS_THRESHOLD:
            verdict = Verdict.PASS
        elif score >= INCONCLUSIVE_THRESHOLD:
            verdict = Verdict.INCONCLUSIVE
        else:
            verdict = Verdict.FAIL

        return ClaimEvaluation(
            claim_id=claim.claim_id,
            evaluator_id="chain_of_verification",
            score=round(score, 4),
            confidence=round(min(1.0, score * CONFIDENCE_SCALE), 4),
            verdict=verdict,
            reasoning=(
                f"CoV: {len(evaluations)} questions evaluated, "
                f"avg score {score:.2f}"
            ),
            evidence=[
                f"Q{i + 1}: {e:.2f}" for i, e in enumerate(evaluations)
            ],
        )

    @staticmethod
    def _fallback_questions(claim: VerificationClaim) -> list[str]:
        """Generate fallback verification questions when LLM fails.

        Args:
            claim: The claim to generate questions for.

        Returns:
            List of generic verification questions.
        """
        return [
            f"Does the context support: {claim.content}?",
            f"Is there evidence against: {claim.content}?",
            f"Are there conditions where {claim.content} is false?",
            "Is the claim internally consistent?",
            "Does the claim align with known facts?",
        ]
