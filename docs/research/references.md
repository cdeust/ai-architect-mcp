# Academic References

Structured bibliography linking AI Architect algorithms to their research foundations.

## Verification Algorithms

### ALG-001: Chain of Verification (CoVe)

- **Paper:** Dhuliawala, S. et al. (2023). "Chain-of-Verification Reduces Hallucination in Large Language Models."
- **Institution:** Meta AI
- **Year:** 2023
- **Key insight:** Generating verification questions about an LLM's own output, then answering them independently, reduces factual errors.

### ALG-002 / ALG-004: Atomic Claim Decomposition

- **Paper:** Min, S. et al. (2023). "FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation."
- **Institution:** University of Washington / Allen Institute for AI
- **Year:** 2023
- **Key insight:** Decomposing text into atomic facts enables precise, per-claim verification rather than holistic scoring.

### ALG-003: Zero-LLM Graph Verification

- **Paper (SCC):** Tarjan, R. E. (1972). "Depth-first search and linear graph algorithms." SIAM Journal on Computing, 1(2), 146-160.
- **Institution:** Cornell University
- **Year:** 1972
- **Paper (GoT):** Besta, M. et al. (2023). "Graph of Thoughts: Solving Elaborate Problems with Large Language Models."
- **Institution:** ETH Zurich
- **Year:** 2023
- **Key insight:** Claim relationships form a DAG; cycles indicate contradictions. Tarjan's SCC algorithm detects these in O(V+E).

### ALG-005: NLI Entailment Evaluator

- **Paper (SNLI):** Bowman, S. R. et al. (2015). "A large annotated corpus for learning natural language inference." EMNLP.
- **Institution:** Stanford University
- **Year:** 2015
- **Paper (MultiNLI):** Williams, A. et al. (2018). "A Broad-Coverage Challenge Corpus for Sentence Understanding through Inference." NAACL.
- **Institution:** New York University
- **Year:** 2018
- **Paper (TRUE):** Honovich, O. et al. (2022). "TRUE: Re-evaluating Factual Consistency Evaluation." NAACL.
- **Institution:** Google Research
- **Year:** 2022
- **Key insight:** Textual entailment classification (entails/contradicts/neutral) provides a principled verification mechanism for claim-premise pairs.

### ALG-006: Multi-Agent Debate

- **Paper:** Du, Y. et al. (2023). "Improving Factuality and Reasoning in Language Models through Multiagent Debate."
- **Institution:** MIT
- **Year:** 2023
- **Key insight:** Multiple LLM agents debating a claim converge toward more factual and well-reasoned conclusions than single-agent generation.

### ALG-007: KS Adaptive Stability Consensus

- **Paper (KS Test):** Kolmogorov, A. N. (1933). "Sulla determinazione empirica di una legge di distribuzione." Giornale dell'Istituto Italiano degli Attuari, 4, 83-91.
- **Institution:** Moscow State University
- **Year:** 1933
- **Paper (Extension):** Smirnov, N. V. (1948). "Table for estimating the goodness of fit of empirical distributions." Annals of Mathematical Statistics, 19(2), 279-281.
- **Year:** 1948
- **Paper (Beta-Binomial):** Gelman, A. et al. (2013). "Bayesian Data Analysis." 3rd ed. Chapman & Hall/CRC.
- **Institution:** Columbia University
- **Year:** 2013
- **Key insight:** KS statistic measures distribution convergence; when evaluator scores stabilize (KS stat below threshold), consensus has been reached.

### ALG-011: Bayesian Consensus

- **Paper:** Gelman, A. et al. (2013). "Bayesian Data Analysis." 3rd ed. Chapman & Hall/CRC.
- **Institution:** Columbia University
- **Year:** 2013
- **Paper (Opinion Pooling):** DeGroot, M. H. (1970). "Optimal Statistical Decisions." McGraw-Hill.
- **Year:** 1970
- **Key insight:** Beta-Binomial conjugate prior enables closed-form posterior updating. Prior beliefs about quality are systematically updated as evaluator evidence accumulates.

### ALG-012: Majority Voting Consensus

- **Paper:** Condorcet, M. de (1785). "Essai sur l'application de l'analyse a la probabilite des decisions rendues a la pluralite des voix."
- **Year:** 1785
- **Key insight:** Condorcet's Jury Theorem — if each voter is more likely right than wrong, majority voting probability of correct decision approaches 1 as voter count increases.

## Prompting Algorithms

### Weighted Average Consensus (Ensemble Baseline)

- **Paper:** Dietterich, T. G. (2000). "Ensemble Methods in Machine Learning." Multiple Classifier Systems, LNCS 1857, 1-15.
- **Institution:** Oregon State University
- **Year:** 2000
- **Key insight:** Combining multiple weak learners via weighted averaging produces a stronger aggregate prediction.

### Adaptive Expansion (Tree/Graph of Thoughts)

- **Paper (ToT):** Yao, S. et al. (2023). "Tree of Thoughts: Deliberate Problem Solving with Large Language Models."
- **Institution:** Princeton University
- **Year:** 2023
- **Paper (GoT):** Besta, M. et al. (2023). "Graph of Thoughts: Solving Elaborate Problems with Large Language Models."
- **Institution:** ETH Zurich
- **Year:** 2023
- **Key insight:** Branching reasoning into tree/graph structures enables exploration of multiple solution paths with backtracking.

### TRM Refinement (Self-Refine)

- **Paper:** Madaan, A. et al. (2023). "Self-Refine: Iterative Refinement with Self-Feedback."
- **Institution:** Carnegie Mellon University
- **Year:** 2023
- **Key insight:** LLMs can iteratively improve their own output through structured self-critique and refinement cycles.

### Signal-Aware Thought Buffer

- **Paper:** Yang, L. et al. (2024). "Buffer of Thoughts: Thought-Augmented Reasoning with Large Language Models."
- **Institution:** Peking University / Microsoft Research
- **Year:** 2024
- **Key insight:** Caching and retrieving relevant thought templates enables efficient reuse of reasoning patterns across similar problems.

### Collaborative Inference

- **Paper (Self-Consistency):** Wang, X. et al. (2022). "Self-Consistency Improves Chain of Thought Reasoning in Language Models."
- **Institution:** Google Research
- **Year:** 2022
- **Paper (DisCIPL):** Chen, J. et al. (2024). "DisCIPL: Disciplined and Calibrated Inference with Pre-trained Language Models."
- **Institution:** MIT
- **Year:** 2024
- **Key insight:** Sampling multiple reasoning paths and selecting the most consistent answer improves reliability over single-path generation.

### Metacognitive Monitoring

- **Paper (Calibration):** Kadavath, S. et al. (2022). "Language Models (Mostly) Know What They Know."
- **Institution:** Anthropic
- **Year:** 2022
- **Paper (Metacognition):** Didolkar, A. et al. (2024). "Metacognitive Capabilities of LLMs: An Exploration in Mathematical Problem Solving."
- **Institution:** Stanford University
- **Year:** 2024
- **Key insight:** LLMs can estimate their own confidence; monitoring these estimates enables intervention when the model is uncertain.

### Confidence Fusion

- **Paper (Self-Consistency):** Wang, X. et al. (2022). "Self-Consistency Improves Chain of Thought Reasoning in Language Models."
- **Institution:** Google Research
- **Year:** 2022
- **Key insight:** Fusing confidence estimates from multiple sources (self-consistency, calibration, evidence strength) produces more reliable uncertainty quantification.

## Future References (Epic 2)

### Experience Pattern Decay

- **Paper:** Ebbinghaus, H. (1885). "Uber das Gedachtnis: Untersuchungen zur experimentellen Psychologie."
- **Year:** 1885
- **Key insight:** Memory retention decays exponentially with time. Half-life parameter controls decay rate: `relevance = initial * 0.5^(elapsed/half_life)`.

### Progressive Disclosure

- **Paper:** Shneiderman, B. (1996). "The Eyes Have It: A Task by Data Type Taxonomy for Information Visualizations." IEEE Symposium on Visual Languages.
- **Institution:** University of Maryland
- **Year:** 1996
- **Key insight:** Present information in layers of increasing detail. L1 (config, 500 tokens) → L2 (summaries, 300 tokens) → L3 (full docs, 3K tokens).
