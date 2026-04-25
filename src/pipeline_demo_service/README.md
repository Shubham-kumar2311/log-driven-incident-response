# Pipeline Demo Service

Standalone microservice for deterministic API-mode end-to-end demo:

1. Log Processing (`/process`)
2. Detection (`/detect`)
3. Incident Management (`/signals`)
4. Response (`/simulate-response`)
5. Actuator (`/execute`)

## Run

```bash
pip install -r requirements.txt
python app.py
```

Default URL: `http://localhost:8016`

Open `http://localhost:8016` to use the standalone dashboard UI.

Dashboard features:
- Run prebuilt logs aligned to detection rules.
- Build a custom event payload with live JSON preview.
- Copy payload JSON for external use.
- View step-by-step pipeline status and raw output.
- Trigger only the processing hop and let downstream services forward naturally.

## Endpoints

- `GET /` (Dashboard UI)
- `GET /api/info`
- `GET /health`
- `GET /demo/prebuilt-logs`
- `GET /demo/pipeline-health`
- `POST /demo/pipeline-run`

`POST /demo/pipeline-run` now triggers processing only. The rest of the chain runs through existing service-to-service forwarding:
processing -> detection -> incident management -> response -> actuator.
