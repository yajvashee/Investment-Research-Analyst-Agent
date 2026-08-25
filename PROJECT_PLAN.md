# Investment Research Analyst Agent — 10-Phase Codex Build Plan

## Project Goal

Build a **single-agent Investment Research Analyst** that can answer questions such as:

- "I have £1,000 to invest. What companies or strategies should I consider?"
- "Compare Microsoft and Apple as investments."
- "Which companies in the system are lower risk?"
- "Build a balanced investment strategy using the companies available."
- "What are the main risks for Microsoft?"
- "How has Nvidia's revenue and EPS changed over time?"

The project must use:

- **Streamlit** — frontend
- **FastAPI** — backend API
- **LangGraph** — agent orchestration
- **LLM** — reasoning and response generation
- **RAG** — company documents / annual reports / 10-K filings
- **Vector store** — embeddings for document retrieval
- **PostgreSQL** — structured historical financial data
- **Finance API** — current/recent market data
- **Docker** — containerisation
- **AWS** — deployment

The system should remain a **single agent**. PostgreSQL, RAG, and the finance API are tools used by that agent.

---

# Codex Working Rules

Codex should follow these rules throughout the project:

1. Work through the phases **in order**.
2. Do not jump ahead to later phases.
3. Before changing code, explain briefly what will be changed.
4. Keep the code understandable for someone learning agentic AI.
5. Prefer simple architecture over unnecessary abstraction.
6. Add comments only where they genuinely help understanding.
7. Do not introduce extra technologies unless they are necessary.
8. Keep secrets and API keys in `.env`.
9. Never commit `.env`, credentials, large raw datasets, or unnecessary generated files.
10. At the end of every phase:
   - run the relevant tests;
   - fix errors;
   - summarize what was built;
   - list the important files;
   - explain how I can manually test it;
   - stop and wait before beginning the next phase.

---

# Target Architecture

```text
                        USER
                          |
                          v
                     STREAMLIT
                     Frontend
                          |
                          v
                      FASTAPI
                      Backend
                          |
                          v
                     LANGGRAPH
                 Investment Agent
                          |
              +-----------+-----------+
              |           |           |
              v           v           v
             RAG      PostgreSQL   Finance API
              |           |           |
              v           v           v
          Documents    Historical    Current /
          / Reports    Financials    Recent Data
              |           |           |
              +-----------+-----------+
                          |
                          v
                         LLM
                          |
                          v
                 Investment Response
```

---

# Suggested Repository Structure

```text
investment-research-agent/
|
|-- app/
|   |-- frontend/
|   |   `-- streamlit_app.py
|   |
|   |-- backend/
|   |   |-- main.py
|   |   `-- schemas.py
|   |
|   |-- agent/
|   |   |-- graph.py
|   |   |-- state.py
|   |   |-- prompts.py
|   |   |-- nodes.py
|   |   `-- tools.py
|   |
|   |-- rag/
|   |   |-- loaders.py
|   |   |-- chunking.py
|   |   |-- embeddings.py
|   |   |-- vectorstore.py
|   |   `-- retriever.py
|   |
|   |-- database/
|   |   |-- connection.py
|   |   |-- models.py
|   |   |-- queries.py
|   |   `-- seed.py
|   |
|   `-- market_data/
|       |-- client.py
|       `-- service.py
|
|-- data/
|   |-- documents/
|   `-- sample/
|
|-- tests/
|
|-- scripts/
|
|-- .env.example
|-- .gitignore
|-- pyproject.toml
|-- uv.lock
|-- docker-compose.yml
|-- Dockerfile.backend
|-- Dockerfile.frontend
|-- README.md
`-- PROJECT_PLAN.md
```

---

# Phase 1 — Project Foundation

## Goal

Create a clean, working Python project before adding any AI or financial logic.

## Tasks

1. Create the repository structure.
2. Initialise the Python environment using `uv`.
3. Create `pyproject.toml`.
4. Add initial dependencies.
5. Create `.gitignore`.
6. Create `.env.example`.
7. Add basic logging.
8. Create a minimal README.
9. Add a simple health-check script.
10. Confirm the project imports correctly.

## Initial Dependencies

Start with the dependencies needed for the early phases. Add others only when required.

Possible packages:

```text
fastapi
uvicorn
streamlit
langgraph
langchain
langchain-openai
sqlalchemy
psycopg
pydantic
pydantic-settings
python-dotenv
httpx
pytest
```

Later RAG dependencies can be added during the RAG phase.

## Environment Variables

Create `.env.example` with placeholders such as:

```text
OPENAI_API_KEY=
FINANCE_API_KEY=

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=investment_agent
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
```

## Acceptance Criteria

Phase 1 is complete when:

- the environment installs successfully;
- Python imports the application modules;
- `.env` is ignored by Git;
- tests can run;
- the folder structure exists;
- no agent logic has been built yet.

---

# Phase 2 — PostgreSQL Historical Financial Database

## Goal

Build the structured-data tool first.

PostgreSQL will store historical company financial information.

## Initial Company Universe

Use a fixed list initially. Keep it easy to change later.

Example:

### Lower-risk / established
- Microsoft — MSFT
- Apple — AAPL
- Coca-Cola — KO

### Medium-risk / growth
- Alphabet — GOOGL
- Amazon — AMZN
- Meta — META

### Higher-growth / higher-volatility
- Nvidia — NVDA
- Tesla — TSLA
- AMD — AMD

The risk labels are **project categories**, not guaranteed investment classifications.

## Database Table

Create a historical financial table containing fields such as:

```text
id
company_name
ticker
fiscal_year
revenue
net_income
total_assets
total_liabilities
total_debt
cash_and_equivalents
shareholders_equity
eps
created_at
```

Optional later metrics:

```text
operating_income
free_cash_flow
gross_margin
operating_margin
```

## Tasks

1. Run PostgreSQL locally.
2. Create SQLAlchemy connection configuration.
3. Create database models.
4. Create table creation / migration logic.
5. Create sample seed data.
6. Create reusable database queries.
7. Add a service function such as:

```python
get_company_financials(ticker: str)
```

8. Add another function such as:

```python
compare_company_financials(tickers: list[str])
```

9. Test database access independently from LangGraph.

## Acceptance Criteria

The following should work before continuing:

```python
financials = get_company_financials("MSFT")
```

It should return clean structured historical data.

Also confirm that invalid tickers fail safely.

---

# Phase 3 — Finance API Tool

## Goal

Connect the project to a finance API for current or recent market data.

## Data Required

Aim for useful market fields such as:

```text
ticker
current_price
market_cap
pe_ratio
52_week_high
52_week_low
price_change
price_change_percent
volume
```

The exact fields depend on the selected API.

## Tasks

1. Select one finance API.
2. Put its key in `.env`.
3. Build a dedicated API client.
4. Add request timeout handling.
5. Add error handling for:
   - invalid ticker;
   - API quota;
   - network error;
   - missing values.
6. Normalize API responses into your own schema.
7. Create:

```python
get_market_data(ticker: str)
```

8. Create:

```python
get_market_data_for_companies(tickers: list[str])
```

9. Add tests using mocked responses where appropriate.

## Important Design Rule

Do not let the rest of the application depend directly on the finance provider's raw JSON.

Convert it into a stable internal format first.

## Acceptance Criteria

This should work independently:

```python
data = get_market_data("MSFT")
```

and return normalized current/recent market information.

---

# Phase 4 — RAG Document Pipeline

## Goal

Build RAG over company reports and filings.

## Documents

Start small.

For each company, use a limited set of high-value documents such as:

- annual reports;
- 10-K filings;
- investor reports;
- company risk disclosures.

Do not start with hundreds of documents.

## Pipeline

```text
Documents
   |
   v
Load / Parse
   |
   v
Metadata
   |
   v
Chunk
   |
   v
Embed
   |
   v
Vector Store
   |
   v
Retrieve
```

## Metadata

Each chunk should retain metadata such as:

```text
company_name
ticker
document_name
document_type
fiscal_year
page_number
section
source
```

## Tasks

1. Add document loaders.
2. Parse PDF/text content.
3. Add structure-aware or recursive chunking.
4. Attach metadata.
5. Generate embeddings.
6. Store embeddings in a vector store.
7. Create a retriever.
8. Add company filtering.
9. Return sources with retrieved chunks.
10. Create:

```python
search_company_documents(
    ticker: str,
    query: str,
    k: int = 5
)
```

## Test Questions

Examples:

```text
"What are Microsoft's main business risks?"

"What does Nvidia say about competition?"

"What growth areas does Amazon highlight?"
```

## Acceptance Criteria

The retriever should return relevant chunks with usable source metadata.

Do not integrate LangGraph until this works independently.

---

# Phase 5 — Convert Data Sources into Agent Tools

## Goal

Create the three tools the Investment Research Analyst agent can call.

## Required Tools

### Tool 1 — PostgreSQL

Purpose:

```text
Historical structured financial data
```

Suggested function:

```python
get_historical_financials(...)
```

### Tool 2 — Finance API

Purpose:

```text
Current/recent market data
```

Suggested function:

```python
get_current_market_data(...)
```

### Tool 3 — RAG

Purpose:

```text
Company reports, risks, strategy, management commentary,
business descriptions and other document evidence
```

Suggested function:

```python
search_financial_documents(...)
```

## Tasks

1. Wrap each underlying service as an agent-compatible tool.
2. Add useful tool descriptions.
3. Validate tool arguments.
4. Return compact structured outputs.
5. Add error handling.
6. Test each tool without the agent.
7. Create tests showing which source each tool retrieves.

## Acceptance Criteria

All three tools can be called independently and return useful information.

At this point the system should conceptually have:

```text
Investment Agent
       |
 +-----+-----+
 |     |     |
DB    RAG   API
```

but LangGraph is not yet responsible for orchestration.

---

# Phase 6 — LangGraph Investment Research Agent

## Goal

Build the single-agent orchestration layer.

Do not build a multi-agent system.

## Initial Graph

Start simple:

```text
START
  |
  v
Understand Request
  |
  v
Research Planner
  |
  v
Tool Execution
  |
  v
Company Analysis
  |
  v
Comparison / Strategy
  |
  v
Final Response
  |
  v
END
```

## Suggested State

The LangGraph state might contain:

```python
user_query
investment_amount
risk_preference
time_horizon
companies
research_plan
tool_results
analysis
recommendation
sources
messages
```

Do not require every field for every question.

## Responsibilities

### Node 1 — Understand Request

Extract things such as:

```text
investment amount
companies mentioned
comparison request
risk preference
time horizon
question type
```

### Node 2 — Research Planner

Determine which information is required.

Example:

```text
Question:
"I have £1,000 to invest. Which companies should I consider?"

Plan:
- compare historical financial strength;
- retrieve current valuations;
- retrieve major company risks;
- rank candidate companies;
- create example allocation.
```

### Node 3 — Tool Execution

Allow the agent to use:

- PostgreSQL;
- RAG;
- finance API.

The system should not blindly call every tool for every question.

### Node 4 — Company Analysis

Calculate or assess metrics such as:

```text
revenue growth
EPS growth
debt position
cash position
profitability
valuation
business risks
```

### Node 5 — Comparison / Strategy

Compare companies and create an appropriate strategy for the user's question.

### Node 6 — Final Response

Produce a clear answer with:

- summary;
- company comparison;
- reasoning;
- risks;
- example allocation where relevant;
- sources;
- disclaimer that this is research/educational information rather than personalized regulated financial advice.

## Acceptance Criteria

This must work from Python before adding FastAPI:

```python
result = agent.invoke(
    {
        "user_query":
        "I have £1,000 to invest. Compare the companies available "
        "and give me a balanced example strategy."
    }
)
```

The result should use real tool outputs rather than inventing financial data.

---

# Phase 7 — FastAPI Backend

## Goal

Expose the working investment agent through a backend API.

## Core Endpoints

Start with:

```text
GET /health
POST /research
```

Optional:

```text
GET /companies
GET /company/{ticker}
```

## Example Request

```json
{
  "question": "I have £1000 to invest. What strategy should I consider?"
}
```

## Example Response Structure

```json
{
  "answer": "...",
  "companies_analyzed": ["MSFT", "AAPL", "GOOGL"],
  "sources": [],
  "tool_usage": [],
  "status": "success"
}
```

## Tasks

1. Create FastAPI application.
2. Add Pydantic request/response schemas.
3. Connect `/research` to LangGraph.
4. Add exception handling.
5. Add logging.
6. Add `/docs` support through FastAPI.
7. Add API tests.
8. Confirm the agent is not recreated unnecessarily on every request.

## Acceptance Criteria

The user can submit a research question through FastAPI Swagger at:

```text
/docs
```

and receive a successful agent response.

---

# Phase 8 — Streamlit Frontend

## Goal

Build a simple, usable investment research UI.

## Main Screen

Include:

- project title;
- question input;
- investment amount;
- optional risk preference;
- optional time horizon;
- analyze button.

## Example Inputs

```text
Investment amount: £1000

Risk preference:
- Lower
- Balanced
- Higher

Time horizon:
- Short
- Medium
- Long

Question:
"What companies or strategy should I consider?"
```

## Output

Display:

1. research summary;
2. companies considered;
3. comparison;
4. example allocation;
5. major risks;
6. sources;
7. disclaimer.

## Important Architecture Rule

Streamlit should **not directly call LangGraph**.

Use:

```text
Streamlit
   |
 HTTP
   v
FastAPI
   |
   v
LangGraph
```

## Tasks

1. Build Streamlit layout.
2. Validate user inputs.
3. Send requests to FastAPI.
4. Handle loading/error states.
5. Render results clearly.
6. Add source display.
7. Add basic UX polish.

## Acceptance Criteria

A user can open Streamlit, enter a question, and receive an answer generated through:

```text
Streamlit -> FastAPI -> LangGraph -> Tools
```

---

# Phase 9 — Docker and Full Local Integration

## Goal

Run the complete project as containers.

## Services

Recommended Docker Compose services:

```text
frontend
backend
postgres
```

A vector database may be added as another service if your chosen RAG architecture requires one.

## Docker Networking

Within Docker:

```text
frontend -> backend
backend -> postgres
```

Do not use `localhost` for container-to-container communication.

Use service names.

Example:

```text
http://backend:8000
```

## Tasks

1. Create backend Dockerfile.
2. Create frontend Dockerfile.
3. Add PostgreSQL to Docker Compose.
4. Configure environment variables.
5. Add persistent PostgreSQL volume.
6. Add health checks.
7. Confirm service startup order.
8. Build all images.
9. Run complete integration test.

## Required Test

After:

```bash
docker compose up --build
```

the user should be able to open Streamlit and submit a research question successfully.

## Acceptance Criteria

The complete local application works only from Docker services.

---

# Phase 10 — Testing, Evaluation, AWS Deployment and Final Documentation

## Goal

Turn the working prototype into a demonstrable final project.

## Part A — Agent Evaluation

Create a small evaluation set.

Examples:

```text
1. Compare Microsoft and Apple.
2. Which company has the strongest revenue growth?
3. What are Microsoft's main reported risks?
4. Which available companies appear financially stronger?
5. I have £1,000 and want a balanced strategy.
6. I have £1,000 and prefer lower risk.
7. Compare Nvidia and Coca-Cola.
8. Which companies have stronger cash positions?
9. What are the main risks of Tesla?
10. Build a diversified example allocation.
```

Evaluate:

```text
tool selection
retrieval relevance
data correctness
groundedness
source quality
response usefulness
failure handling
```

## Part B — Safety / Financial Boundaries

The system must:

- avoid presenting uncertain forecasts as facts;
- distinguish historical/current data from model judgement;
- show data sources;
- state important assumptions;
- avoid guaranteeing returns;
- make clear that outputs are informational/educational research, not personalized regulated financial advice.

## Part C — AWS Deployment

Choose the simplest architecture that meets the course requirements.

Possible deployment components may include:

```text
ECR
ECS / App Runner / EC2
RDS PostgreSQL
S3
```

The exact services should be selected based on the training requirements and allowed AWS architecture.

## Part D — Documentation

Finish `README.md` with:

1. problem statement;
2. architecture;
3. technologies;
4. setup instructions;
5. environment variables;
6. PostgreSQL setup;
7. RAG ingestion;
8. API configuration;
9. running locally;
10. running with Docker;
11. example questions;
12. screenshots;
13. limitations;
14. future improvements.

## Part E — Final Demonstration

The final demo should show:

```text
1. User opens Streamlit.
2. User enters £1,000.
3. User selects balanced risk.
4. User asks for an investment strategy.
5. Streamlit sends request to FastAPI.
6. FastAPI invokes LangGraph.
7. LangGraph decides which tools to call.
8. PostgreSQL returns historical financials.
9. Finance API returns current/recent market data.
10. RAG returns relevant company evidence.
11. Agent compares companies.
12. Agent produces an example strategy.
13. User sees reasoning, risks and sources.
```

## Acceptance Criteria

The project is complete when:

- Streamlit works;
- FastAPI works;
- LangGraph works;
- PostgreSQL works;
- RAG works;
- finance API works;
- the tools are called correctly;
- Docker works;
- the system has been tested;
- AWS deployment works;
- the README explains the entire project;
- the final demonstration can be reproduced.

---

# Phase Summary

| Phase | Main Outcome |
|---|---|
| 1 | Project foundation |
| 2 | PostgreSQL historical financials |
| 3 | Finance API |
| 4 | RAG system |
| 5 | Three working agent tools |
| 6 | LangGraph single agent |
| 7 | FastAPI backend |
| 8 | Streamlit frontend |
| 9 | Docker integration |
| 10 | Evaluation, AWS and final documentation |

---

# Instructions to Give Codex

When using this file with Codex, use the following instruction:

```text
Read PROJECT_PLAN.md fully before making changes.

We are building this project one phase at a time.

Only work on the current phase I specify.
Do not implement later phases early.

For the current phase:

1. Inspect the existing repository first.
2. Tell me what already exists.
3. Explain the changes you are going to make in simple language.
4. Implement the phase.
5. Keep the code simple enough for me to understand and explain.
6. Run the appropriate tests/checks.
7. Fix any errors.
8. Summarize every file you created or changed.
9. Explain how I can test the phase manually.
10. Stop after completing the phase.

Do not proceed to the next phase until I explicitly tell you to.
```

---

# First Codex Prompt

Once this file is saved at the root of the repository, start with:

```text
Read PROJECT_PLAN.md.

We are starting Phase 1 only.

I currently have little or no code, so inspect the repository first.

Complete Phase 1: Project Foundation.

Keep the architecture simple and explain what you are doing because I need to understand and present this project myself.

Do not start Phase 2.
```

---

# Core Principle

Do not try to build the entire application at once.

The development sequence is:

```text
Data
 |
 v
Tools
 |
 v
Agent
 |
 v
Backend
 |
 v
Frontend
 |
 v
Containers
 |
 v
Deployment
```

Each layer should work independently before the next layer is added.

# demo test
