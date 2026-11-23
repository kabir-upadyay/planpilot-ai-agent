# PlanPilot AI

**Intelligent Task Planning and Dynamic Replanning Agent** — Agentic AI, Unit II, CO II

PlanPilot turns a complex goal into an ordered, dependency-aware task plan, compares two scheduling strategies, and demonstrates a transparent five-stage ReAct loop. A simulated campus venue failure lets you observe assumption checking, tool use and dynamic replanning. The app runs locally without paid APIs.

## Features

- Decomposes five included planning scenarios and custom goals into tasks with descriptions, priorities, dependencies, durations and statuses.
- Compares sequential and dependency-aware schedules with estimated duration, resource approach and risk.
- Steps through THINK, ACT, OBSERVE, EVALUATE and REPLAN, with a concise user-facing rationale. Hidden chain-of-thought is not exposed.
- Runs simulated tools for venue availability, resource search, budgets and task scheduling.
- Triggers an auditorium outage, identifies affected tasks, selects an available venue based on availability, cost and capacity, updates the plan and continues execution.
- Offers pause, resume, step-by-step execution, reset, progress metrics and an activity timeline.
- Uses a transparent deterministic rule-based engine. No LLM is called and no API key is required.

## Architecture

```text
React + Vite dashboard (localhost:5173)
        │ JSON REST API
        ▼
FastAPI application (localhost:8000)
        ├── Goal decomposition and strategy evaluation
        ├── ReAct simulation and task dependency state
        └── Simulated venue, budget and scheduling tools
```

The simulation state is held in the browser and sent to the API with each action; restarting the browser resets the session. The backend has no database or external AI dependency.

## Technology

React 18, Vite 6, custom responsive CSS, Lucide icons, Python 3.10+, FastAPI, Pydantic and Uvicorn.

## Run locally

Requirements: Python 3.10+, Node.js 20+ and npm.

Terminal 1 (API):

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Terminal 2 (frontend):

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173. The API health endpoint is http://127.0.0.1:8000/api/health and interactive API docs are at http://127.0.0.1:8000/docs.

## Use the demo

1. Choose a suggested goal or enter a custom goal and build a plan.
2. Compare the two strategies, task dependencies and the selected rationale.
3. Start execution or step through each action. Pause and resume from the execution controls.
4. For the technical event scenario, trigger the auditorium outage. Review the failed assumption, affected work and venue selection, then keep stepping through the revised plan.
5. Use Reset to begin a fresh simulation.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Engine status |
| GET | `/api/scenarios` | Included goals |
| POST | `/api/plan` | Decompose a goal and compare strategies |
| POST | `/api/step` | Execute one ReAct task step |
| POST | `/api/event` | Trigger and respond to the venue outage |
| POST | `/api/replan` | Replan after a triggered event |
| POST | `/api/control/pause` or `/resume` | Pause or resume execution |

## Assignment mapping

- **Chain-of-Thought concept:** summarized, user-facing decision rationale only; private hidden reasoning is not displayed.
- **Tree-of-Thought concept:** compare two candidate schedules and select one using critical-path duration and coordination risk.
- **ReAct:** API actions append observable THINK, ACT, OBSERVE, EVALUATE and REPLAN events to the execution timeline.
- **CO II:** ordered subtasks, strategy evaluation, tool-mediated actions and recovery after a violated assumption.

## Testing

Run API and agent behavior checks from the project root:

```powershell
python -m pip install -r backend/requirements.txt
python -m pytest backend/tests -q
```

Build the frontend:

```powershell
cd frontend
npm install
npm run build
```

## Student

Kabir Upadhyay · ADT23SOCB0495 · Roll 17 · Agentic AI · Unit II · CO II
