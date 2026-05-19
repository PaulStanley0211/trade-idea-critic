# SSE event schema

`GET /api/v1/critique/{request_id}/stream` returns an `text/event-stream` connection that emits the events below as the LangGraph pipeline progresses. The stream closes when a `final` or `error` event is sent.

Reconnection: clients may reconnect by issuing a fresh GET; replay is not supported (V1). If the run already finished, the server replies `200` with `final` (or `error`) and closes.

## Event format

All events follow the standard SSE shape:

```
event: <name>
data: <JSON payload>

```

(Trailing blank line ends an event. JSON payloads are single-line.)

## Events

### `status`

Coarse-grained pipeline-phase update. Useful for the UI's top-line state.

```json
{ "phase": "parsing | planning | specialists | synthesizing | critiquing | finalizing", "message": "Parsing thesis..." }
```

### `node_started`

Fired when a LangGraph node begins. Maps 1:1 to `app.agents.*` module names.

```json
{ "node_name": "structure_critic" }
```

### `node_completed`

Fired when a node finishes successfully. The `summary` is a 1-2 sentence prose summary that the UI can show in a timeline; `partial_state_keys` lists which `CritiqueState` fields the node populated, so the UI can light up sections as they fill.

```json
{
  "node_name": "structure_critic",
  "summary": "R/R 2.7, stop within 0.6 ATR — mechanics are clean.",
  "partial_state_keys": ["structure"]
}
```

### `final`

Terminal success event. Payload is a complete `CritiqueResponse` (see `app/models/api.py` and `openapi.json`).

```json
{ "request_id": "...", "status": "complete", "verdict": "marginal", "raw_thesis": "...", "sections": { ... }, ... }
```

### `error`

Terminal failure event. After this, the stream closes.

```json
{ "code": "parser_failed | critic_loop_exceeded | cost_cap_reached | upstream_unavailable | internal", "message": "Free-text explanation safe to show the user.", "recoverable": false }
```

## Frontend handling

The client (`frontend/app/c/[request_id]/page.tsx`) uses the browser's native `EventSource`. Pattern:

```ts
const es = new EventSource(`/api/v1/critique/${id}/stream`);
es.addEventListener("status",         (e) => onStatus(JSON.parse(e.data)));
es.addEventListener("node_started",   (e) => onNodeStarted(JSON.parse(e.data)));
es.addEventListener("node_completed", (e) => onNodeCompleted(JSON.parse(e.data)));
es.addEventListener("final",          (e) => { onFinal(JSON.parse(e.data)); es.close(); });
es.addEventListener("error",          (e) => { onError(e); es.close(); });
```

Note that the `error` event name overlaps with the EventSource native error (connection drop). Distinguish by inspecting whether `e.data` is present (server-sent) vs. absent (transport-level).
