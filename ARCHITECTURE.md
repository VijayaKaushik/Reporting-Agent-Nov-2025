# Architecture overview — langgraph-report-framework (app/)

This document explains the high-level architecture in `app/` and gives concrete, copy-paste guidance for new developers on how to add Agents and Tools.

## Goals
- Provide a clear mental model of the runtime: orchestrator (graph) → agents (nodes) → tools/services (workers/clients).
- Document the minimal contract for Agents and Tools so developers can add new ones quickly.
- Show where to register components and how the orchestrator invokes them.

## File map (important files)
- `app/orchestrator.py` — Builds a langgraph StateGraph using agents, compiles it and exposes `run_graph(thread_id, payload)`.
- `app/agents/` — Agent implementations and registry.
  - `base_agent.py` — `BaseAgent` abstract class and hooks.
  - `registry.py` — Simple in-memory registration (`init_agents`, `get_agent`).
  - `template_agent.py` — Example agent that picks templates using a tool and the LLM.
  - `planning_agent.py` — (commented) planning/intent classification example.
- `app/tools/` — Tools that agents can call. Two possible patterns are used:
  - LangChain-style tool functions (see `fetch_template.py` using `@tool` decorator).
  - `BaseTool` abstract class (defined in `base_tool.py`) for object-based tools.
- `app/services/` — Thin clients for backend services (DB, templates). Example: `template_service_client.py`.
- `app/llm.py` — LLM wrapper (uses Google Gemini via `google-generativeai`).
- `app/config.py` — Loads environment/settings.
- `app/state.py` — `GraphState` TypedDict: canonical state keys used by agents.
- `app/main.py` — small entry script (prints a greeting), not the orchestrator.

## Core concepts and runtime flow
1. `orchestrator.build_graph()` calls `init_agents()` to register agent instances.
2. It creates a `StateGraph` and adds nodes. Each node's callable delegates to `get_agent(<name>).execute(state)`.
3. `StateGraph.invoke(state, config=...)` executes nodes in order. The `checkpointer` can persist state between steps.
4. Agents may call Tools (local functions or clients) and the LLM via `llm_complete()`.

Because nodes are regular callables returning a dict (state updates), composition and testing are straightforward.

## Agent contract (BaseAgent)
Any new Agent should inherit `BaseAgent` and implement at least:
- name(self) -> str — unique node name used in the graph and registry.
- system_prompt(self) -> str — a short string describing the agent role (for LLMs).
- execute(self, state: Dict[str, Any]) -> Dict[str, Any] — main behavior: read/modify/return state.

Optional hooks/methods:
- tools(self) -> List[Callable] — list of tool functions the agent might call.
- pre_hook(self, state) / post_hook(self, state) — pre/post processing.
- on_error(self, state, error) — error handler.

Minimal success criteria for an agent
- Must not raise unhandled exceptions (prefer try/except and set `state['status']='error'` and `state['error']`).
- Should update `state` using keys from `app/state.GraphState` where applicable (e.g., `status`, `reply`, `candidate_templates`).

### Example: new agent (skeleton)

Create `app/agents/my_new_agent.py`:

```python
from typing import Dict, Any
from app.agents.base_agent import BaseAgent

class MyNewAgent(BaseAgent):
    def name(self) -> str:
        return "my_new_agent"

    def system_prompt(self) -> str:
        return "Help do X given user input"

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # read inputs
        query = state.get("user_message", "")
        # perform work (tools, LLM calls, services)
        state["reply"] = "I processed the request"
        state["status"] = "done"
        return state
```

Then register the agent in `app/agents/registry.py` by adding it to the `init_agents()` list:

```python
from app.agents.my_new_agent import MyNewAgent

def init_agents():
    for agent in [TemplateAgent(), MyNewAgent()]:
        _REGISTER[agent.name()] = agent
```

Finally, add a node to the graph in `app/orchestrator.py` and an edge so the flow hits it:
```python
g.add_node("my_new_agent", lambda s: get_agent("my_new_agent").execute(s))
# add edges accordingly
```

## Tool contract
There are two patterns in the repo:

1) LangChain tool function (used by `TemplateAgent`):
   - Add a function in `app/tools/` and decorate it with `@tool("tool_name", return_direct=False)` from `langchain.tools`.
   - Return the value the agent expects (e.g., a list/dict).

Example (function tool):

```python
from langchain.tools import tool
from typing import List, Dict

@tool("my_fetcher", return_direct=False)
def my_fetcher_tool(query: str) -> List[Dict]:
    # call a service or DB
    return [{"id": "1", "name": "example"}]
```

2) BaseTool class (object based):
   - Implement `BaseTool` in `app/tools/base_tool.py` and implement `name()` and `run()`.
   - Agents can instantiate or import the tool and call `tool.run(...)`.

Example (class tool):
```python
from app.tools.base_tool import BaseTool

class MyTool(BaseTool):
    def name(self) -> str:
        return "my_tool"

    def run(self, **kwargs):
        return {"result": 123}
```

Which approach to pick?
- Use LangChain `@tool` if you want tools to be available to LLM-agent tool-choosing flows.
- Use `BaseTool` for simple service wrappers or when you want to maintain internal state/instances.

## Services
- Put thin wrappers that communicate with external systems in `app/services/` (e.g., DB, HTTP clients).
- Agents and tools call service functions (e.g., `template_service_client.list_templates()`).

## LLM usage
- Use `app/llm.llm_complete(prompt)` which wraps Google Generative AI (Gemini). The API key and model name come from environment variables: `GOOGLE_API_KEY`, `GEMINI_MODEL` configured in `app/config.py`.

## Registration and discovery
- The current registry is simple: `init_agents()` instantiates agents and stores them in a dict `_REGISTER` keyed by `agent.name()`.
- To add dynamic/discoverable plugins later you can switch to scanning modules or using entry-points, but for now editing `registry.py` is the straightforward method.

## Testing and local verification
- Keep `execute()` logic small and side-effect free where possible; test logic with unit tests that call `agent.execute(state)`.
- Example test (pytest style):

```python
from app.agents.template_agent import TemplateAgent

def test_template_agent_returns_candidates():
    agent = TemplateAgent()
    state = {"user_message": "demographics report"}
    out = agent.execute(state)
    assert "candidate_templates" in out
```

## Environment & running
- Python version: the `pyproject.toml` target indicates `requires-python = ">=3.13"`. Use a supported Python or adjust as needed.
- Set environment variables (e.g., in `.env`):
  - `GOOGLE_API_KEY` — required for `app/llm.py` to call Gemini
  - `GEMINI_MODEL` — model name
- Run local quick test: from repo root

```bash
python -m app.main
# or run the orchestrator in a small harness
python -c "from app.orchestrator import run_graph; print(run_graph('t1', {'message':'hello'}))"
```

## Troubleshooting & tips
- If `llm` calls hang or fail, set `GOOGLE_API_KEY` and confirm network access.
- When adding an agent, if the graph never reaches the node, ensure you've added edges correctly in `orchestrator.build_graph()`.
- If you want persistent checkpointer or production storage, replace `InMemorySaver()` with a durable saver supported by langgraph.

## Recommended small follow-ups (improvements)
- Convert `agents.registry.init_agents()` to a dynamic importer (scan `app/agents` and import classes by convention).
- Add unit tests that run a one-node graph and assert state transitions.
- Add a simple CLI test harness under `scripts/` that runs `run_graph()` with sample payloads.

---

If you want, I can also:
- Add a template `tests/test_template_agent.py` and run it.
- Wire a small CLI (script) to run orchestrator flows with sample JSON payloads.

File created: `ARCHITECTURE.md` — let me know if you'd like a different filename or location.
