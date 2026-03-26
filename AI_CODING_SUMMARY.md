# AI Coding Session Summary & Iteration Log

*Note: This document serves as the formal summary of the AI workflows, prompting techniques, and architectural iterations executed during the development of this Forward Deployed Engineer Assignment.*

## 1. How AI Tools Were Utilized
The entire project was built leveraging advanced Agentic AI workflows (specifically Antigravity/Gemini architectures) functioning in "CTO-mode"—operating heavily autonomously rather than relying on standard sequential code autocomplete.

- **Infrastructure as Code (IaC):** The AI agent was tasked to automatically generate PostgreSQL Docker containers, write data ingestion scripts, and execute them dynamically against remote production databases (Render).
- **Full-Stack Orchestration:** The agent independently scaffolded a React `Vite` environment using native `react-force-graph-2d` overlays, connecting entirely to the autonomous FastAPI backend without human intermediate intervention.

## 2. Key Prompts and Workflows
The project was executed through segmented, high-level structural prompts outlining specific phases:

- **Phase 1 (Data & Infrastructure):** "Build an automated ingestion pipeline that correctly models disconnected raw ERP JSON payloads (`sap-o2c-data`) into strict relational PostgreSQL tables modeling orders, deliveries, invoices, and payments linked by foreign keys."
- **Phase 2 (LLM Pipeline Generation):** "Create a sophisticated GenAI backend pipeline featuring explicit Intent Guardrails. The pipeline must reject unrelated prompts entirely, then programmatically write synthetic PostgreSQL queries matching the schema bounds, execute them safely, and translate the data into natural language."
- **Phase 3 (Visual Graph Logic):** "Construct a UI with a 70/30 split. The left panel utilizes HTML5 Canvas rendering to layout an interconnected nodes graph (limited dynamically to 50 nodes to prevent browser crashing). Node colors must be explicitly mapped to entities (e.g., Order=Blue, Delivery=Green)."
- **Phase 4 (Interactive Chat State):** "Synchronize the React chat input with the `POST /query` backend limiters. Whenever the SQL queries return actionable IDs, automatically pass those mappings (`highlight_nodes`) back to the Graph component and trigger targeted visual highlighting animations against the active paths."

## 3. Debugging and Iteration Cycles
Several complex iteration and deployment roadblocks were debugged dynamically by the AI agent during the build sequence:

- **Cross-Platform Dependency Failures:** During deployment to the native Render Linux environment, the build failed due to Windows-specific libraries (`pywin32`, `pefile`) being accidentally frozen into the requirements list. The AI agent identified the OS mismatch, utilized regex filtering loops to re-encode the `.txt` from `UTF-16LE` to `UTF-8`, and purged the mismatched dependencies allowing the Docker container to deploy flawlessly.
- **SQL Parsing Limitations:** When initial datasets were too broad, `LEFT JOIN` aggregations crashed. The AI iterated to inject a self-healing pipeline where execution crashes are caught and fed back into the SQL generator prompt, actively appending strict `LIMIT 10` clamps or syntactical fixes dynamically.
- **Security & Environmental Isolation:** The agent detected a hardcoded `GEMINI_API_KEY` mapped directly into the Python orchestrators. To strictly adhere to deployment best practices, a refactor loop was initiated to rip the keys out into `.env` contexts, update the GitHub `.gitignore` parameters, and configure environment variables in Render/Vercel natively.
