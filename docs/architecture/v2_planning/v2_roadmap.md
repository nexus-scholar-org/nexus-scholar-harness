# The "Strangler Fig" V2 Roadmap

To transition Nexus Scholar Harness to V2 safely, we will use the "Strangler Fig" pattern. This ensures you always have a working system and never break the reliable 8 research kits.

## Step 1: Lay the Foundation (Branching & Tooling)
* **Goal:** Create a safe sandbox and pick the engine.
* **Action:** Create a `v2-next` branch. Leave the 8 kits completely alone. Pick an orchestrator framework (e.g., Prefect, Temporal, or a custom Python `asyncio` task queue).

## Step 2: The "Parity" Rewrite (Focus on Scale)
* **Goal:** Replicate V1's behavior but with a distributed engine.
* **Action:** Rewrite `src/scholar_harness/orchestrator.py` so that it uses the new async task queue. Wrap each kit call (e.g., calling `scholar-search`) into a discrete async task. 
* **Validation:** Run a test with 50 papers and ensure it processes them concurrently instead of linearly, and perfectly writes to `audit/journal.jsonl`.
* *Result: You now have the Scale of V2, but the behavior of V1.*

## Step 3: The API & Dashboard (Focus on Usability)
* **Goal:** Build the Researcher Command Center.
* **Action:** Build a thin **FastAPI** layer that reads your workspace files (`protocol.json`, `journal.jsonl`) and serves them as JSON endpoints. Boot up a **Vite (React) + Tailwind** project. Build a "Mission Control" dashboard that consumes this API to show a live feed of your parallel agents working.
* *Result: You now have a visual platform UI instead of a CLI.*

## Step 4: The Supervisor Brain (Focus on Autonomy)
* **Goal:** Make the system self-healing and dynamic.
* **Action:** Build the "Chief Orchestrator Agent" (an LLM that reads the protocol and dynamically decides which tasks to queue up in Step 2). Give it error-handling capabilities (e.g., if the PDF kit fails, the Supervisor spins up a search agent to look for a preprint).
* *Result: The system is now truly autonomous.*
