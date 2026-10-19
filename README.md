# AgentFlow — Multi-Agent Customer Support Ticket Management

CA-3 | Domain-specific Agentic AI Proof of Concept | Python + Streamlit | No API key required

## Problem
Manual ticket triage is slow and inconsistent: agents read, classify, prioritize, search for solutions, draft replies and check quality. AgentFlow demonstrates an offline, auditable workflow using cooperating **mock agents** and synthetic tickets.

## Main features
- Single-ticket and CSV batch intake using 10 synthetic samples
- Planner → Classifier → Priority → Research → Resolution → Critic workflow
- Evidence-backed categories, priority escalation, knowledge lookup and response draft
- Human-review routing for critical/high-risk/ambiguous cases
- Decision trace JSON, downloadable results CSV, operations dashboard
- Built-in safety constraint: **never sends replies automatically**

## Quick start (Windows PowerShell)
```powershell
cd AgentFlow_CA3
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Open the local address printed by Streamlit (usually http://localhost:8501).

### macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

## Demo walkthrough
1. Open **Process a ticket** and choose `TKT-1006` (fraud). Click **Run agent workflow**: expect Critical → Human Review.
2. Choose `TKT-1003` (delivery delay): expect Delivery & Shipping → Draft Ready.
3. Review the Planner, decision evidence, KB reference, draft and Critic rationale.
4. Open **Batch processing**, run the bundled 10-ticket dataset and export results.
5. See **Operations dashboard** for priority/category charts.

## Code structure
```
app.py                     Streamlit interface + dashboard
agentflow/core.py          Six specialized agents and orchestrator
agentflow/__init__.py      Public interfaces
data/sample_tickets.csv    Fictional examples
tests/test_core.py         Unit tests
AgentFlow_CA3_Report.docx  Academic report
AgentFlow_CA3_Presentation.pptx Slides
assets/architecture.png    Workflow figure
```

## Run tests
```bash
python -m pytest -q
```

## Approach and limitations
This is a **rule-based mock-model**, not an LLM, trained ML classifier or production helpdesk. Keywords may misclassify sarcasm, multilingual messages or overlapping categories. Category confidence is a heuristic, not a calibrated probability. Synthetic test cases do not establish real-world business improvements. The PoC has no customer integrations, user authentication, persistence or automatic replies. Knowledge base text is illustrative and not a company policy. Real deployments require security review, human oversight, calibrated evaluation, access controls and privacy compliance.

## GitHub submission
1. Create a new **public** repository named `AgentFlow-CA3` on GitHub.
2. Upload **all files and folders** from this repository, retaining the folder structure.
3. Add the repository URL to the assignment portal; optional screenshots can go in `assets/`.
4. Verify `README.md`, `.docx`, `.pptx`, code and dataset appear on GitHub.

**Do not upload** `.venv`, passwords, credentials, API tokens or real customer information.
