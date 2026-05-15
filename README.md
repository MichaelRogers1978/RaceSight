# RaceSight

RaceSight is a motorsport intelligence system for race strategy, driver coaching, safety analysis, and what-if simulation. This repository includes a Granite-based orchestrator that selects tools, validates payloads, dispatches RaceSight functions, and returns structured responses.

## What is in this repo

- `ai/`: Granite tool schemas, orchestrator configs, adapters, prompts, and validation helpers
- `analytics/`: predictive and scoring model surfaces
- `core/`: canonical race, telemetry, track, and event model surfaces
- `dashboard/`: presentation-layer components
- `simulation/`: telemetry and race simulation surfaces
- `main.py/`: orchestrator entrypoint scripts
- `docs/`: architecture and model documentation

## Granite integration

The Granite orchestration path is centered on these files:

- `ai/granite_orchestrator_agent_config.embedded.json`: self-contained system prompt and tools
- `ai/granite_orchestrator_loader.py`: payload builder and HTTP sender for Granite
- `main.py/orchestrator_main.py`: orchestration loop, tool dispatch, and validated execution
- `ai/schema_usage.py`: strict tool parameter validation before execution
- `ai/pydantic_models.py`: Pydantic models for RaceState and tool payloads

## Environment variables

Set these before live Granite calls:

- `GRANITE_ENDPOINT`: Granite chat/tool-calling endpoint
- `GRANITE_API_KEY`: bearer token or compatible API credential

Start from `.env.example` and copy the values you need into your local environment setup.

You can also pass endpoint, key, and model via CLI flags.

Example PowerShell session setup from `.env.example` values:

```powershell
$env:GRANITE_ENDPOINT = "https://your-granite-endpoint"
$env:GRANITE_API_KEY = "your-api-key"
$env:GRANITE_MODEL = ""
```

## Running the orchestrator

Print the first-turn Granite payload without sending a request:

```powershell
& ".venv/Scripts/python.exe" "main.py/orchestrator_main.py" "What should we do now?" --print-payload-only
```

Run the orchestrator against a live Granite endpoint:

```powershell
$env:GRANITE_ENDPOINT = "https://your-granite-endpoint"
$env:GRANITE_API_KEY = "your-api-key"

& ".venv/Scripts/python.exe" "main.py/orchestrator_main.py" "Is it safe?"
```

## Repository setup

Recommended first push workflow:

1. Create a private GitHub repository.
2. Initialize git locally.
3. Review `git status` before the first commit.
4. Confirm `.venv/`, secrets, and local artifacts are excluded.
5. Push `main` to the private remote.

For private-to-public publishing safety, follow the checklist in `SECURITY.md` before making the repository public.

## Notes

- Prompt files under `ai/prompts/` can be customized per agent role.
- Some AI module files currently use fallback prompts if their prompt files are empty.
- The repository is structured for incremental migration from simulated data toward real telemetry sources.
