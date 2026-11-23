"""PlanPilot's transparent, deterministic planning and ReAct simulation API."""
from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="PlanPilot AI", version="1.0.0", description="Rule-based task planning and ReAct workflow simulator")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])

SCENARIOS = {
    "event": ("Organize a college technical event", [
        ("Choose event date", "Set a date that works for organizers and speakers.", "High", 1, []),
        ("Book auditorium", "Reserve the main college venue for the event.", "High", 1, ["Choose event date"]),
        ("Arrange technical equipment", "Confirm microphones, projector and network access.", "High", 2, ["Book auditorium"]),
        ("Contact speakers", "Invite technical speakers and confirm availability.", "Medium", 3, ["Choose event date"]),
        ("Open registrations", "Publish attendee registration and capacity details.", "Medium", 1, ["Book auditorium"]),
        ("Finalize event schedule", "Combine talks, breaks and venue logistics.", "High", 2, ["Arrange technical equipment", "Contact speakers", "Open registrations"]),
    ]),
    "trip": ("Plan a three-day college trip", [("Choose destination", "Agree on a destination and dates.", "High", 2, []), ("Estimate budget", "Estimate transport, lodging and food costs.", "High", 1, ["Choose destination"]), ("Book transport", "Compare and reserve suitable transport.", "High", 2, ["Estimate budget"]), ("Reserve accommodation", "Find lodging for the group.", "High", 2, ["Choose destination", "Estimate budget"]), ("Collect permissions", "Gather student and college approvals.", "Medium", 3, ["Choose destination"]), ("Prepare itinerary", "Schedule activities across three days.", "Medium", 2, ["Book transport", "Reserve accommodation"])]),
    "software": ("Complete a software development project", [("Define requirements", "Document goals, users and constraints.", "High", 2, []), ("Design architecture", "Choose components and define interfaces.", "High", 2, ["Define requirements"]), ("Implement core features", "Build the essential product workflows.", "High", 5, ["Design architecture"]), ("Write automated checks", "Cover key success and failure paths.", "Medium", 2, ["Define requirements"]), ("Review and fix issues", "Validate the integrated application.", "High", 2, ["Implement core features", "Write automated checks"]), ("Prepare release", "Document installation and package the result.", "Medium", 1, ["Review and fix issues"])]),
    "birthday": ("Organize a birthday party", [("Choose date and guest list", "Select a convenient date and invitees.", "High", 1, []), ("Set budget", "Allocate spending across venue, food and decor.", "High", 1, []), ("Book venue", "Reserve a space sized for the guest list.", "High", 2, ["Choose date and guest list"]), ("Order food and cake", "Confirm menu and cake delivery.", "Medium", 2, ["Set budget", "Choose date and guest list"]), ("Arrange decorations", "Prepare a decoration plan for the venue.", "Low", 2, ["Book venue"]), ("Share final schedule", "Send guests the final party timing.", "Medium", 1, ["Order food and cake", "Arrange decorations"])]),
    "exam": ("Prepare for a college examination", [("List syllabus topics", "Break the syllabus into study units.", "High", 1, []), ("Assess current knowledge", "Identify strong and weak topics.", "High", 1, ["List syllabus topics"]), ("Create revision schedule", "Allocate study blocks based on topic difficulty.", "High", 1, ["Assess current knowledge"]), ("Study priority topics", "Revise the topics that need the most attention.", "High", 5, ["Create revision schedule"]), ("Practice past questions", "Apply knowledge under exam-like conditions.", "Medium", 3, ["Study priority topics"]), ("Review errors and rest", "Fix recurring gaps and reserve time for rest.", "Medium", 2, ["Practice past questions"])]),
}
VENUES = [{"name": "Auditorium", "capacity": 500, "cost": 0, "available": True, "equipment": 5}, {"name": "Innovation Hall", "capacity": 220, "cost": 3500, "available": True, "equipment": 4}, {"name": "Seminar Room B", "capacity": 120, "cost": 1200, "available": True, "equipment": 3}, {"name": "Open Air Amphitheatre", "capacity": 300, "cost": 1800, "available": True, "equipment": 2}]

class PlanRequest(BaseModel):
    goal: str = Field(min_length=8, max_length=240)

class EventRequest(BaseModel):
    event: str = "auditorium_unavailable"
    state: dict

class StepRequest(BaseModel):
    state: dict

class StateRequest(BaseModel):
    state: dict

def build_plan(goal: str) -> dict:
    key = next((k for k in SCENARIOS if any(term in goal.lower() for term in ({"event": ["event", "technical"], "trip": ["trip"], "software": ["software", "development", "project"], "birthday": ["birthday", "party"], "exam": ["exam", "study"]}[k]))), None)
    title, rows = SCENARIOS[key] if key else (goal.strip().rstrip(".!?"), [("Clarify the desired outcome", f"Define measurable success criteria for: {goal}", "High", 1, []), ("List constraints and resources", "Identify time, budget, people and resource limits.", "High", 1, ["Clarify the desired outcome"]), ("Break work into milestones", "Convert the goal into small verifiable deliverables.", "High", 2, ["List constraints and resources"]), ("Complete the first milestone", "Start with the highest-priority unblocked deliverable.", "High", 2, ["Break work into milestones"]), ("Review progress and adjust", "Compare results with the goal and refine next steps.", "Medium", 1, ["Complete the first milestone"])])
    tasks = [{"id": f"T{i}", "name": n, "description": d, "priority": p, "duration_days": t, "dependencies": deps, "status": "pending", "replanned": False} for i,(n,d,p,t,deps) in enumerate(rows, 1)]
    parallel = sum(t[3] for t in rows); sequential = sum(t[3] for t in rows)
    longest = max((sum(next(x[3] for x in rows if x[0] == dep) for dep in r[4]) + r[3] for r in rows), default=parallel)
    strategies = [{"name":"Sequential focus", "duration_days":sequential, "risk":"Low", "resource":"One owner at a time", "reason":"Simple to coordinate, but independent work waits in line."}, {"name":"Dependency-aware parallel", "duration_days":max(longest, (sequential+1)//2), "risk":"Moderate", "resource":"Two work streams", "reason":"Runs independent tasks together while respecting prerequisites."}]
    chosen = "Dependency-aware parallel" if strategies[1]["duration_days"] < sequential else "Sequential focus"
    return {"id":str(uuid4()), "goal":goal, "title":title, "tasks":tasks, "strategies":strategies, "selected_strategy":chosen, "rationale":"The plan starts with high-priority prerequisites, then unlocks dependent work. The selected schedule shortens the critical path without violating task dependencies.", "stage":"READY", "events":[], "replanning_count":0, "paused":False, "event_triggered":False, "venues":deepcopy(VENUES), "venue":"Auditorium" if "event" in title.lower() else None}

@app.get("/api/health")
def health(): return {"status":"ok", "engine":"transparent-rule-based", "llm_enabled":False}

@app.get("/api/scenarios")
def scenarios(): return [{"id":k,"title":v[0]} for k,v in SCENARIOS.items()]

@app.post("/api/plan")
def create_plan(req: PlanRequest): return build_plan(req.goal)

def log(state: dict, stage: str, title: str, detail: str, tool: str | None = None):
    state["stage"] = stage
    state["events"].append({"id":str(uuid4()),"stage":stage,"title":title,"detail":detail,"tool":tool,"step":len(state["events"])+1})

@app.post("/api/step")
def execute_step(req: StepRequest):
    s=deepcopy(req.state); tasks=s.get("tasks", []); pending=[t for t in tasks if t["status"]=="pending" and all(any(x["name"]==d and x["status"]=="completed" for x in tasks) for d in t["dependencies"])]
    if s.get("paused"): raise HTTPException(409,"Execution is paused")
    if not pending: raise HTTPException(409,"No unblocked tasks remain")
    task=pending[0]
    log(s,"THINK",f"Prioritize: {task['name']}",f"This {task['priority'].lower()} priority task is unblocked and advances the goal. Dependencies are satisfied.")
    tool="check_venue_availability" if task["name"]=="Book auditorium" else "check_budget" if "budget" in task["name"].lower() else "schedule_task"
    log(s,"ACT",f"Run {tool}()",f"The agent invokes {tool} for {task['name']}.",tool)
    if task["name"]=="Book auditorium":
        chosen=next((v for v in s["venues"] if v["name"]==s.get("venue")),None)
        result=f"{chosen['name']} is available with capacity {chosen['capacity']}." if chosen and chosen["available"] else f"{s.get('venue','Auditorium')} is unavailable."
    else: result=f"{task['name']} is scheduled in the dependency-aware queue; estimated effort {task['duration_days']} day(s)."
    log(s,"OBSERVE", "Tool result received",result)
    if task["name"]=="Book auditorium" and not next((v for v in s["venues"] if v["name"]==s.get("venue") and v["available"]),None):
        log(s,"EVALUATE","Assumption violated","The selected venue is unavailable, so venue-dependent tasks cannot proceed.")
        s=perform_replan(s)
    else:
        task["status"]="completed"
        log(s,"EVALUATE","Outcome matches plan","The action succeeded and prerequisite state is now recorded.")
        if not any(t["status"]=="pending" for t in tasks): log(s,"THINK","Goal complete","All planned tasks are complete.")
    return s

def perform_replan(s: dict):
    available=[v for v in s.get("venues",[]) if v["available"] and v["name"]!="Auditorium"]
    if not available: log(s,"REPLAN","No suitable alternative","No available venue meets the scenario constraints."); return s
    venue=sorted(available,key=lambda v:(v["cost"],-v["capacity"]))[0]
    affected=[t["name"] for t in s["tasks"] if t["name"] in ("Book auditorium","Arrange technical equipment","Open registrations","Finalize event schedule")]
    original_booking_name=next(t["name"] for t in s["tasks"] if t["name"]=="Book auditorium")
    revised_booking_name=f"Book {venue['name']}"
    for t in s["tasks"]:
        if original_booking_name in t["dependencies"]:
            t["dependencies"]=[revised_booking_name if dep==original_booking_name else dep for dep in t["dependencies"]]
        if t["name"]==original_booking_name: t.update(name=revised_booking_name,description=f"Reserve {venue['name']} (capacity {venue['capacity']}; simulated cost {venue['cost']}).",status="completed",replanned=True)
        elif t["name"] in ("Arrange technical equipment","Open registrations","Finalize event schedule"): t["replanned"]=True
    s["venue"]=venue["name"]; s["replanning_count"]+=1
    log(s,"REPLAN","Plan revised",f"Failed assumption: Auditorium availability. Trigger: venue unavailable. Affected work: {', '.join(affected)}. {venue['name']} is selected: capacity {venue['capacity']}, cost {venue['cost']}, available equipment score {venue['equipment']}/5. Venue-dependent work resumes after replacement booking.")
    return s

@app.post("/api/event")
def trigger_event(req: EventRequest):
    s=deepcopy(req.state)
    if s.get("event_triggered"): raise HTTPException(409,"Unexpected event was already triggered")
    venue=s.get("venue")
    if not venue: raise HTTPException(400,"Choose the technical event scenario to trigger the venue event")
    for v in s["venues"]:
        if v["name"]==venue: v["available"]=False
    s["event_triggered"]=True
    log(s,"OBSERVE","Unexpected event","The auditorium is suddenly unavailable. The initial availability assumption is no longer valid.")
    log(s,"EVALUATE","Check plan impact","Venue booking, equipment setup, registrations and final scheduling depend on a confirmed venue.")
    log(s,"ACT","Run check_resource_availability()","Search the simulated campus venue inventory for replacements.","check_resource_availability")
    s=perform_replan(s)
    return s

@app.post("/api/replan")
def replan(req: StateRequest):
    s=deepcopy(req.state)
    if not s.get("event_triggered"): raise HTTPException(409,"No violated assumption to replan around")
    return perform_replan(s)

@app.post("/api/control/{action}")
def control(action: str, req: StateRequest):
    s=deepcopy(req.state)
    if action=="pause": s["paused"]=True; log(s,"PAUSED","Execution paused","The workflow will wait until resumed.")
    elif action=="resume": s["paused"]=False; log(s,"READY","Execution resumed","The agent can continue with the next unblocked task.")
    else: raise HTTPException(404,"Unknown control action")
    return s
