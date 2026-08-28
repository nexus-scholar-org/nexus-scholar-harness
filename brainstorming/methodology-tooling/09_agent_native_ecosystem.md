# Agent-Native Ecosystem (Nexus for Agents)

## Overview
Instead of building a traditional web application (GUI) for humans, we package the entire Nexus Scholar pipeline as an **Agent-Native Ecosystem**. We expose the CLI kits as MCP (Model Context Protocol) servers and Antigravity Skills so that *any* autonomous AI agent (Antigravity, OpenDevin, Claude Desktop, etc.) can act as the researcher's autonomous research assistant.

## The Paradigm Shift
Humans are bottlenecks in large-scale literature reviews. A human clicking a button to "Extract 150 PDFs" and waiting 20 minutes is inefficient.
If we build for agents:
1. The human simply says: *"I want to run a systematic review on how AI affects learning. Find me the papers, screen them, and write a PRISMA report."*
2. The AI Agent autonomously invokes the `scholar-search-kit` tool.
3. The AI Agent autonomously feeds the results to `scholar-screen-kit`.
4. The AI Agent autonomously triggers `scholar-pdf-kit` to extract the full texts.
5. The AI Agent autonomously queries `scholar-rag-kit` to synthesize the final answer.

## Detailed Specs for Agent Integration

### 1. Model Context Protocol (MCP) Servers
We expose the capabilities of the kits as standard MCP tools. Any agent that supports MCP can instantly "install" the Nexus Scholar pipeline.
* **Tool: `nexus_discover`**: Takes a research query and returns 2,000 DOIs.
* **Tool: `nexus_screen`**: Takes a list of DOIs and inclusion criteria, and returns the filtered PRISMA list.
* **Tool: `nexus_extract`**: Takes a DOI, downloads the PDF, runs Docling, and returns raw Markdown.
* **Tool: `nexus_query_rag`**: Takes a factual or methodological query and searches the indexed literature.

### 2. Antigravity Skills & Plugins
For the Antigravity IDE specifically, we can bundle these tools into a formal **Plugin** (`C:\Users\mouadh\.gemini\config\plugins\nexus-scholar`).
The plugin would contain:
* `mcp_config.json`: Pointing to our Python-based MCP servers.
* `skills/`:
  * `skill-systematic-review`: Teaches the agent the exact 5-step workflow for executing a systematic review using the Nexus tools.
  * `skill-methodology-audit`: Teaches the agent how to use the `scholar-rag-kit` to audit a paper's rigor metrics.

### 3. The "Headless" Advantage
By building for agents instead of building a web app:
* **Zero UI Code:** We don't have to build React components, dashboards, or handle WebSocket state management. We just expose pristine APIs and CLI tools.
* **Maximum Composability:** Researchers can integrate the Nexus tools with other agent skills (like `pubmed-database` or `literature-search-openalex`) seamlessly.
* **Infinite Scalability:** An agent can run a background task overnight to download and extract 10,000 PDFs without human intervention.

## Conclusion
Building an Agent-Native ecosystem is exponentially faster than building a web app and aligns perfectly with the future of autonomous research. We transform the Nexus Scholar kits into the "operating system" for AI research assistants.
