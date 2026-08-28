# From Harness to Production Web App ("Nexus Science")

## Overview
While a Typer CLI is excellent for power users and automation, to reach the scale of a production app like "Claude" or "Elicit," the Nexus Scholar Harness must be decoupled into a backend orchestrator and a rich, interactive frontend. 

## 1. Architecture: The Backend (FastAPI / Agent Framework)
The Python CLI we discussed in `07_nexus_scholar_harness.md` becomes a headless API.
* **Orchestrator Engine:** We wrap the existing `scholar-*-kit` Python packages using **FastAPI**. 
* **State Management:** Because literature screening and PDF extraction take minutes/hours, the backend must use an asynchronous task queue (like **Celery** or **RabbitMQ**). 
* **The Agent Layer:** The LLM agents (`methodology-copilot`, `three-pass-triage`) are hosted behind WebSockets to provide real-time, streaming conversational responses just like Claude.

## 2. Architecture: The Frontend (React / Next.js)
To deliver a premium, Claude-like experience, the frontend needs to be built with modern web technologies (e.g., **Next.js** or **Vite**).

### Core UI Workflows:
1. **The Copilot Interface (Phase 1):** A sleek, chat-like interface where the user talks to the `methodology-copilot`. The UI dynamically renders the generated `preregistration.md` file side-by-side as they chat.
2. **The Funnel Dashboard (Phase 2):** A visual pipeline showing the status of the literature. 
   - A block showing "2,000 DOIs Found".
   - A Kanban-style screening board where the AI sorts abstracts into "Included" and "Excluded".
   - A progress bar showing real-time Docling PDF extraction.
3. **The Interactive RAG Viewer (Phase 3):** The killer feature. When the user queries the database, the UI doesn't just return text; it returns *interactive PDF snippets*. It highlights the exact table or methodology paragraph in the original PDF, overlaid with the graph network showing how this paper relates to others.

## 3. The Path to Production
To turn this into a reality, we would follow this sequence:
1. **APIization:** Wrap `scholar-search-kit`, `scholar-pdf-kit`, and `scholar-rag-kit` in a FastAPI backend.
2. **Web App Foundation:** Initialize a Vite or Next.js React app.
3. **Design System:** Implement a premium, dark-mode aesthetic with micro-animations that feels cutting-edge.
4. **Integration:** Connect the WebSocket chat interface to the backend RAG and Copilot agents.
