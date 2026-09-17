# Nexus Scholar Harness: V2 Architecture Specification

To achieve the "Holy Trinity" of Scale, Usability, and Autonomy, V2 must evolve from a linear, CLI-driven script into a distributed, agent-native web platform. This document outlines the technical architecture and strategic decisions discussed during the V2 planning phase.

## 1. Scale: The Distributed Swarm Architecture
To handle tens of thousands of papers without choking, we need to move away from synchronous, single-threaded processing.

- **Workflow Engine Backbone:** Replace `orchestrator.py` with a lightweight asynchronous task queue (e.g., Celery, arq, or a native Python `asyncio` + Redis setup) or a robust engine like **Prefect**.
- **Parallel Agent Swarms:** Instead of one agent processing `batch_NNN.json`, the orchestrator spawns a swarm of workers via direct LLM API calls.
  - *Example:* 100 concurrent instances of the `ScreeningAgent` can hit the LLM APIs simultaneously, reducing PRISMA screening from hours to minutes.
- **Vector DB Scaling:** Upgrade the local `scholar-rag-kit` from in-memory/local ChromaDB to a scalable vector store (e.g., Qdrant or Milvus) to support massive, concurrent RAG queries during synthesis.

## 2. Usability: The Researcher's Command Center
CLI is great for engineers, but researchers need a beautiful, interactive, and transparent UI.

- **Frontend Tech Stack:** A modern web app built with **Next.js or Vite (React)** + **Tailwind CSS**. 
- **Real-Time Telemetry:** The `audit/journal.jsonl` file becomes the source of truth for an SSE (Server-Sent Events) stream. The UI features a live "Mission Control" terminal where researchers can watch agents working in real-time.
- **Interactive Graphing:** The `scholar-graph-kit`'s static PyVis HTML output is upgraded to a native React graph library (like React Flow or Cytoscape.js). Users can click nodes (papers) to instantly see the AI's extraction summary.
- **Human-in-the-Loop Triage:** An intuitive Tinder-style UI (swipe left to exclude, right to include) for when the autonomous agents flag a paper as "edge case - needs human review."

## 3. Autonomy: The Supervisor Agent
To make the system truly autonomous, it needs a "brain" that manages the other agents, rather than relying on a hardcoded pipeline.

- **The Supervisor Pattern:** We introduce a Chief Orchestrator Agent. You give it the `protocol.json`, and it figures out the execution graph.
- **Dynamic Routing:** 
  - If a paper has no PDF, the Supervisor dispatches the `SearchAgent` to find alternate open-access routes.
  - If the `VerifyAgent` flags a paper for high risk-of-bias, the Supervisor automatically assigns a `DeepCritiqueAgent` to do a secondary analysis.
- **Self-Healing:** If an API rate limit is hit or an extraction fails, the Supervisor catches the error, applies backoff strategies, or rewrites the prompt to try again—without crashing the whole pipeline.

---

## Architectural Decisions & Q&A

### Q1: Why use raw LLM APIs when we have IDE Agents (like OpenCode)?
While IDE agents are great for planning (like acting as a Socratic wizard during inception), they are not suitable for the massive data execution phase of a systematic review.
1. **Portability (Phase 7 Requirement):** Relying on proprietary IDE subagents locks the tool to the IDE. Using standard LLM APIs (`openai`, `litellm`) allows the orchestrator to run anywhere (headless Linux servers, CI/CD, etc.).
2. **Scientific Predictability:** IDE agents are autonomous problem solvers that might unpredictably use tools. Raw APIs with `response_format={"type": "json_object"}` guarantee deterministic, structured JSON extraction required for scientific rigor.
3. **Throughput:** Spawning 1,000 IDE agents simultaneously is too heavy. Firing 1,000 async HTTP calls to an LLM API is lightweight and lightning fast.

**The Golden Rule:** Use IDE Agents as the researcher/planner, and use LLM APIs as the robotic assembly line for extraction.

### Q2: Which tasks should use small, cheap models vs. large frontier models?
A smart V2 orchestrator routes tasks intelligently to save cost and time:

**Tasks for Tiny/Small Models (2B - 8B parameters like Gemini Flash, Llama 3 8B):**
- **Title & Abstract Screening:** Simple binary classification ("Does this abstract mention machine learning?").
- **Data Formatting:** Pulling explicit numbers (sample sizes, P-values) from a text chunk into JSON.
- **Deduplication:** Comparing two citation strings to see if they match (if not using traditional fuzzy string matching).

**Tasks for Large/Frontier Models (Gemini Pro, Claude Sonnet/Opus):**
- **Risk of Bias Assessment:** Deep scientific reasoning to determine if a study's blinding methodology was robust.
- **Grounded Synthesis (Phase 6):** Reading 50 extraction summaries and writing a cohesive academic literature review.
- **Protocol Design:** The interactive inception phase where the model helps formulate epistemological paradigms.
