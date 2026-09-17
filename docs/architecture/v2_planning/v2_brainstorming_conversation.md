# V2 Brainstorming Q&A Transcript

**Date:** 2026-09-14

This document captures the raw Q&A conversation regarding the V2 Architecture.

---

**Q: Is it necessary to use LLM with API when the whole thing runs in a harness like OpenCode? Why need LLM API?**

**A:** If you already have a powerful AI agent like me (or OpenCode) sitting right here in your IDE, why would the harness need to call out to external LLM APIs (like OpenAI, Gemini, or Anthropic APIs)?

The short answer is the difference between the **"Chief Architect" (Me)** and the **"Factory Workers" (The APIs)**. 

Here is exactly why an LLM API is necessary for Version 2 to achieve the **Scale** and **Autonomy**:

1. **Concurrency and Speed (Scale):** I am a single, synchronous conversational agent. I can only do one thing at a time. If you have 5,000 academic PDFs to screen for your literature review, having me read them one by one in this chat interface would take days. By using an LLM API, the harness code can spin up **100 parallel requests** at the exact same time. The API can process 100 papers simultaneously in seconds.
2. **Context Window Pollution:** Every time we talk or I read a file, it uses up my "context window". If I try to read 5,000 PDFs in this chat, my memory will get completely overloaded. An API allows the harness to send 5,000 *isolated* requests. The API reads one paper, extracts the data, and forgets it.
3. **Cost and Specialization:** I am a very large, expensive "reasoning" model designed for complex problem-solving. Using a model like me to do simple, repetitive tasks is overkill. With an API, the harness can route simple tasks to lightning-fast, cheap models.
4. **Background Automation (Autonomy):** I am designed to talk to *you*. But for true autonomy, you want a system that can run overnight while you sleep. The LLM APIs allow the Python code to programmatically "talk" to the AI in the background, parse the JSON responses, handle errors, and move on to the next step without ever needing a chat interface.

---

**Q: But OpenCode can spawn multi agents, each has an independent context window?**

**A:** It is absolutely true that OpenCode (and systems like me) can spawn independent subagents, each with their own clean context window. Why still wire the Python code to talk to raw LLM APIs?

The decision comes down to **Portability**, **Scientific Rigor**, and **Throughput**:

1. **Portability (The "Run Anywhere" Requirement):** You are in Phase 7 (Distribution/Portability). If the Python code relies on OpenCode's proprietary "spawn subagent" feature, then Nexus Scholar can **only** ever run inside the OpenCode IDE. If you use standard LLM APIs (like `openai` or `litellm`), a researcher can run `uv run scholar-screen` on a headless Linux server, in a GitHub Actions pipeline, or on a basic laptop.
2. **Scientific Rigor and Predictability:** IDE Subagents are autonomous problem solvers. If you tell an IDE subagent to "extract data from this PDF," it might decide to use a web-search tool or write a python script. Raw LLM APIs allow you to strictly enforce output using things like "Structured JSON Mode" or Pydantic schemas. You want a deterministic "thin" request that guarantees a perfect JSON object comes back.
3. **Throughput Overhead:** Spawning a subagent initiates a full cognitive loop, provisions tool access, and creates logging streams. Trying to spawn 1,000 subagents in the IDE at once would likely throttle the system. Direct HTTP calls to an API are incredibly lightweight.

**The Perfect Compromise:** Use IDE Agents for the **planning phase** (designing the protocol interactively) and use API calls in the Python Kits for the **execution phase** (crunching 1,000 PDFs).

---

**Q: Which tasks need only small fast models, and how small can the model be?**

**A:** In a Systematic Literature Review (SLR) pipeline, routing the right task to the right size model saves budget and time.

**Tasks for Small Models (2B - 8B parameters like Gemini Flash, Llama 3 8B):**
1. **Title & Abstract Screening (PRISMA Step 1):** Reading a 250-word abstract and answering a binary question ("Does this paper discuss supervised machine learning?"). Extremely small, fine-tuned models can do this flawlessly.
2. **Data Formatting & Entity Extraction:** Scanning a methodology section and pulling out explicit facts (sample sizes, P-values) as JSON. Fast models are exceptionally good at following strict JSON schemas without needing deep reasoning.
3. **Deduplication & Citation Merging:** Looking at two messy BibTeX entries and deciding if they match. Often handled by standard Python fuzzy matching, but a tiny 2B LLM can catch tricky edge cases.

**Tasks for Large Models (Gemini Pro, Claude Sonnet/Opus):**
1. **Risk of Bias Assessment:** Deep scientific reasoning to determine if a study's blinding methodology was robust enough to prevent selection bias.
2. **Grounded Synthesis:** Taking 50 different data extractions and synthesizing them into a cohesive, academically rigorous literature review.
3. **Protocol Design:** Acting as the "Socratic Wizard" to help you define your inclusion criteria.
