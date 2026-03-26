# Architecture & Approach

This document outlines the architectural decisions, database modeling, and LLM prompting strategies utilized to build the context graph system and conversational AI interface.

## 1. Architectural Decisions

The system is built on a segregated **React Frontend** and **FastAPI Python Backend** architecture. This decoupling ensures the heavy-lifting of LLM inference and SQL generation remains entirely on the server, keeping the client lightweight and secure.

- **Frontend (React + Vite):** Selected for its fast iteration speeds and robust component ecosystem. We utilize `react-force-graph-2d` for rendering high-density node clusters natively on an HTML5 Canvas, which prevents DOM overhead from crashing the browser when mapping large Order-to-Cash (O2C) flows.
- **Backend (FastAPI):** Chosen for its native asynchronous capabilities and automatic Pydantic validation. The backend serves both the `/api/graph/all` endpoint (feeding the overarching graph UI) and the central `/query` endpoint (handling the conversational graph interactions).
- **Communication:** Communication occurs synchronously via REST. Node relationships derived analytically by the backend are transmitted to the frontend via arrays of node IDs, triggering local UI reactivity.

## 2. Database Choice & Graph Modeling

We operate a **relational PostgreSQL database** that natively models the graph relationships via foreign keys, rather than relying on a native Graph Database (like Neo4j). 

**Why PostgreSQL?**
- **Structured Predictability:** ERP datasets (like SAP flows) are inherently structured with strongly typed schemas. Storing Orders, Deliveries, and Invoices in relational tables ensures strict data integrity.
- **Implicit Graphs via Joins:** We can dynamically derive a robust, interconnected graph system simply by performing recursive `LEFT JOIN` operations across the lineage (`products` ➔ `order_items` ➔ `orders` ➔ `deliveries` ➔ `invoices`).
- **Performance:** For read-heavy analytical dashboards tracking structural lineages, traditional indexing over constrained keys operates extremely efficiently.

The `trace_order_flow()` backend logic extracts graph nodes by dynamically mapping the connections between entities during inference limits, allowing scalable UI rendering.

## 3. LLM Prompting Strategy

The conversational integration utilizes a **Stateful LLM Pipeline** modeled closely on a standard orchestrator. Instead of a single zero-shot call, the AI agent employs multiple specialized passes:

1. **Intent Extraction:** The LLM first grades the incoming user prompt to determine if it is an analytical question, a trace request, or an out-of-bounds message. 
2. **SQL Generation Agent:** If valid, an agent generates synthetic SQL matching the strict schema bounds (Orders, Invoices, Deliveries). It is explicitly instructed to retrieve relationship keys alongside aggregate counts.
3. **Execution & Feedback Loop:** The backend validates the SQL (e.g., forcing a `LIMIT`). If PostgreSQL throws a syntax error, the error is retrieved and passed *back* to the LLM agent to self-heal the query dynamically.
4. **Natural Language Translation:** The raw data block extracted from the database is fed back into the LLM context exclusively to translate the SQL table payload into a polished, human-readable answer.

## 4. Guardrails & Safety Mechanisms

Given the necessity of preventing hallucinations, strict pipeline guardrails were implemented:

- **Isolated Intent Layer:** The pipeline intercepts non-contextual prompts (e.g., *"Write a poem"*) completely at layer 1. The LLM flags a `PURE_GUARDRAIL_BLOCK` instruction, halting the pipeline natively before it attempts to parse imaginary tables.
- **Read-Only Restrictions:** The SQL validation layer restricts commands like `DROP`, `DELETE`, or `UPDATE`.
- **Hallucination Prevention:** The Natural Language response is solely grounded on the SQL payload. If the database returns `0` rows, the LLM is explicitly barred from generating synthetic answers; it instead notifies the user the mapped flow returned zero correlations.
- **Visual Confidence Indexing:** The API returns `highlight_nodes`, pushing visual correlation into the graph UI. If an LLM hallucinates an answer, the UI will immediately expose the logic gap by highlighting zero corresponding anchor points, forcing mechanical accountability.
