# Code-review prompt for Trade-Idea Critic

Use this prompt to review every change before it merges to `main`. Run it in the IDE with the diff loaded as context. After the review, wait 12 hours and re-read the verdict before merging (the cooling-off rule from `PLAN.md` §4).

---

You are reviewing a change to the Trade-Idea Critic, an agentic system that critiques trader theses for US, Indian, and German equities. The project's binding rules live in `CLAUDE.md` and `PLAN.md` — those documents take precedence over your generic instincts.

**Your job:** read the diff, then produce a structured verdict. Do not rewrite the code; flag issues and let the author fix them.

## Inputs you should consult before reviewing

- `CLAUDE.md` — conventions (no emoji, uv only, function/module size limits, etc.).
- `PLAN.md` — scope, architecture, success criteria.
- `docs/setups/orb.md` and `docs/setups/sr_bounce.md` — setup rules, when the diff touches a specialist.
- The relevant `backend/app/llm/client.py` invariants when the diff touches any LLM call.

## Checklist (every item is binding)

### Conventions
- [ ] No Unicode emoji in source, comments, commits, logs, critiques, dashboard, or docs.
- [ ] Type hints on every public Python function. Docstrings on modules and non-trivial functions.
- [ ] No `print` calls — `loguru` only.
- [ ] No commented-out blocks. No dead code. No TODOs without a tracking issue.
- [ ] Functions under ~40 lines. Modules under ~300 lines.
- [ ] `ruff check` and `mypy` zero warnings on touched Python files.
- [ ] `eslint` and `tsc --noEmit` zero warnings on touched TS files.
- [ ] No `pip install` anywhere (uv only). Dependencies added via `uv add` and committed to `uv.lock`.

### Architecture invariants
- [ ] LangGraph nodes are pure functions of `CritiqueState`. Side effects go through `app/memory/` or `app/tools/` only.
- [ ] All LLM calls go through `app/llm/client.py`. No direct `anthropic.*` imports elsewhere.
- [ ] All DB access goes through `app/memory/`. No raw SQL outside repository modules; queries are parameterized.
- [ ] No HTTP calls inside agent nodes — only via `app/tools/`.
- [ ] External text (news, filings, market data text) wrapped in `<source>...</source>` before being included in prompts.

### Critic + safety
- [ ] If the diff changes the synthesizer or any specialist output: confirm the critic still runs on the new fields and verifies quantitative claims.
- [ ] No bypass path around the critic.
- [ ] Output filter still blocks "buy / sell / recommend." If language was added, confirm the filter and the critic rewrite path still cover it.
- [ ] Cost-cap guard intact: every new LLM call counted toward the daily budget via `app/llm/client.py`.

### Tests
- [ ] New code is covered by unit tests in `backend/tests/unit/` (math, parsing, schema, repository logic).
- [ ] Integration paths covered in `backend/tests/integration/` with cassette replay (no live network in CI).
- [ ] Property-based tests via hypothesis where numerical correctness matters (R/R, ATR, base-rate lookups).
- [ ] Tests are meaningful — they assert specific outputs, not just "no exception."
- [ ] Coverage on `backend/app/` stays at or above 80%.

### Prompts
- [ ] New or modified prompts live under `backend/prompts/` with a version suffix (`_vN.md`).
- [ ] When a prompt changes, the eval-compare run is attached to the PR and the new version wins on agreement vs. the previous version.

### Frontend
- [ ] Components are typed against the generated `frontend/lib/api.ts`; no `any` smuggling.
- [ ] SSE event handlers cover all five event types (`status`, `node_started`, `node_completed`, `final`, `error`).
- [ ] No client-side fetch of `ANTHROPIC_API_KEY` or any backend-only secret. Only `NEXT_PUBLIC_*` vars on the client.

### Security and data
- [ ] No secrets logged. LLM prompt/response logs scrubbed of API keys.
- [ ] No string interpolation into SQL — parameterized via SQLAlchemy.
- [ ] EDGAR client sends `User-Agent` and respects rate limits.
- [ ] Submitted theses retention respected (90-day default).

## Output format

```
## Verdict
APPROVE | REQUEST CHANGES | NEEDS DISCUSSION

## Must-fix
- File:line — issue and why it violates a binding rule.

## Should-fix
- File:line — issue worth fixing but not a merge blocker.

## Nits
- File:line — style or minor improvement.

## Notes
Anything the author should think about that isn't a defect.
```

If the diff is large enough that you cannot review it carefully in one pass, say so and ask for it to be split. Do not approve a diff you have not fully read.
