"""Signal-Aware Thought Buffer — template-based reasoning enhancement.

Research: Yang et al. (2024) Buffer of Thoughts.
"""

from __future__ import annotations

from ai_architect_mcp._models.prompting import EnhancedPrompt

LEARNING_THRESHOLD = 0.8
DEFAULT_MODEL = "claude-sonnet-4-20250514"


class ThoughtTemplate:
    """A reusable thought template with success tracking."""

    def __init__(
        self,
        template_id: str,
        category: str,
        pattern: str,
        success_rate: float = 0.5,
    ) -> None:
        self.template_id = template_id
        self.category = category
        self.pattern = pattern
        self.success_rate = success_rate
        self.usage_count = 0


class SignalAwareThoughtBuffer:
    """Signal-aware thought buffer for template-based enhancement."""

    def __init__(self, client: object, model: str = DEFAULT_MODEL) -> None:
        if client is None:
            raise ValueError(
                "SignalAwareThoughtBuffer requires an LLM client. "
                "Provide a Claude CLI client or AsyncAnthropic instance."
            )
        self._client = client
        self._model = model
        self._templates: list[ThoughtTemplate] = self._default_templates()
        self._learned: list[ThoughtTemplate] = []

    async def process(self, prompt: str, context: str) -> EnhancedPrompt:
        """Process a prompt using thought buffer templates.

        Args:
            prompt: The original prompt.
            context: Supporting context.

        Returns:
            EnhancedPrompt with template-enhanced version.
        """
        templates = self._retrieve_templates(prompt, context)
        enhanced_context = self._build_enhanced_context(prompt, context, templates)
        result = await self._execute(enhanced_context)

        confidence = await self._evaluate_confidence(result, context)
        if confidence > LEARNING_THRESHOLD:
            self._learn(prompt, result, confidence)

        for t in templates:
            t.usage_count += 1

        return EnhancedPrompt(
            original=prompt,
            enhanced=result,
            strategy_used="thought_buffer",
            confidence=round(confidence, 4),
            iterations=1,
        )

    def _retrieve_templates(
        self, prompt: str, context: str
    ) -> list[ThoughtTemplate]:
        """Retrieve relevant templates by keyword matching.

        Args:
            prompt: The prompt to match against.
            context: Supporting context.

        Returns:
            Up to 3 relevant templates.
        """
        prompt_lower = prompt.lower()
        relevant: list[ThoughtTemplate] = []
        for template in self._templates + self._learned:
            if any(
                kw in prompt_lower
                for kw in template.category.lower().split("_")
            ):
                relevant.append(template)
        if not relevant and self._templates:
            relevant = sorted(
                self._templates, key=lambda t: -t.success_rate
            )[:2]
        return relevant[:3]

    def _build_enhanced_context(
        self,
        prompt: str,
        context: str,
        templates: list[ThoughtTemplate],
    ) -> str:
        """Build enhanced context from templates.

        Args:
            prompt: The original prompt.
            context: Supporting context.
            templates: Selected templates to apply.

        Returns:
            Enhanced context string.
        """
        template_text = "\n".join(
            f"Pattern ({t.category}): {t.pattern}" for t in templates
        )
        return (
            f"{prompt}\n\nContext:\n{context}\n\n"
            f"Applicable patterns:\n{template_text}"
        )

    async def _execute(self, enhanced_context: str) -> str:
        """Execute the enhanced prompt.

        Args:
            enhanced_context: The enhanced context to execute.

        Returns:
            Execution result.
        """
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                temperature=0.7,
                system=(
                    "You are an expert content generator. Execute the task "
                    "described below, applying the provided patterns and context "
                    "to produce thorough, well-structured output."
                ),
                messages=[{
                    "role": "user",
                    "content": enhanced_context,
                }],
            )
            return response.content[0].text.strip()
        except (AttributeError, IndexError, TypeError):
            return enhanced_context
        except Exception:
            return enhanced_context

    async def _evaluate_confidence(self, result: str, context: str) -> float:
        """Evaluate confidence in the result.

        Args:
            result: The execution result.
            context: Supporting context.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=50,
                temperature=0.1,
                system=(
                    "Rate the quality of this result on a scale of 0.0 to 1.0. "
                    "Respond with only a number."
                ),
                messages=[{
                    "role": "user",
                    "content": (
                        f"Result:\n{result[:2000]}\n\n"
                        f"Context:\n{context[:1000]}"
                    ),
                }],
            )
            text = response.content[0].text.strip()
            score = float(text.split()[0].strip(".,;:"))
            return max(0.0, min(1.0, score))
        except (AttributeError, IndexError, TypeError, ValueError):
            return 0.7
        except Exception:
            return 0.7

    def _learn(self, prompt: str, result: str, confidence: float) -> None:
        """Learn a new template from a successful execution.

        Args:
            prompt: The prompt that succeeded.
            result: The successful result.
            confidence: The confidence achieved.
        """
        template = ThoughtTemplate(
            template_id=f"learned_{len(self._learned)}",
            category="learned",
            pattern=prompt[:100],
            success_rate=confidence,
        )
        self._learned.append(template)

    def _default_templates(self) -> list[ThoughtTemplate]:
        """Create the default template library.

        Returns:
            List of built-in thought templates.
        """
        return [
            ThoughtTemplate(
                "t1", "analysis",
                "Break the problem into components, analyze each independently",
                0.8,
            ),
            ThoughtTemplate(
                "t2", "verification",
                "Verify each claim against evidence before proceeding",
                0.85,
            ),
            ThoughtTemplate(
                "t3", "architecture",
                "Consider ports/adapters pattern and dependency direction",
                0.75,
            ),
            ThoughtTemplate(
                "t4", "security",
                "Check for injection, authentication, and data protection",
                0.9,
            ),
            ThoughtTemplate(
                "t5", "testing",
                "Write tests first, then implement to satisfy them",
                0.82,
            ),
        ]
