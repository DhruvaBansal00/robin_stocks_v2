# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

# Project-specific instructions

`robin_stocks_v2` is a Python SDK for the Robinhood / Gemini / TDA APIs (`robin_stocks/`) plus an MCP server that exposes the SDK as tools (`robin_stocks_mcp/`). `setup.py` is the build source; `python_requires>=3.10`.

## Environment setup

```bash
pip install -e ".[mcp,dev]"
```

This installs the package, the `mcp` extra (`mcp[cli]`), and the `dev` extra (pytest + pytest-asyncio/timeout/dotenv/cov). Use a virtualenv — the system Python is externally managed (PEP 668).

## Tests

Two distinct kinds of tests live under `tests/` — know which you're touching:

- **Unit tests** (`tests/sdk/`, `tests/mcp/`) — fully mocked, offline, no credentials. **This is what CI runs and what you must keep green:**
  ```bash
  pytest tests/sdk tests/mcp
  ```
- **Integration tests** (`tests/test_robinhood.py`, `tests/test_gemini.py`, `tests/test_tda.py`) — hit live broker accounts using credentials from env/`.test.env`. **Not run in CI; never required to pass for a PR.** Don't add CI steps that depend on them.

pytest config lives in `pytest.ini` (`asyncio_mode=auto`). When you add behavior, add a unit test under `tests/sdk` or `tests/mcp` that mocks the network (see existing tests for the `unittest.mock` patterns).

## Linting & formatting (ruff)

Ruff is the single lint+format tool. Config is in `ruff.toml`. **CI pins `ruff==0.15.14`** — install that exact version locally so results match.

```bash
ruff check .          # lint  (CI gate: must be clean)
ruff format --check .  # format check (CI gate: must be clean)
ruff check --fix .     # apply safe autofixes
ruff format .          # apply formatting
```

Config summary and the reasoning behind it (don't "fix" these without cause):

- `line-length = 127`, `target-version = "py310"`.
- Rules selected: `E`, `W` (pycodestyle), `F` (pyflakes), `I` (isort), `UP` (pyupgrade), `B` (bugbear).
- **Ignored, intentionally:**
  - `F403` / `F405` — the SDK re-exports its public API via `from .module import *`. Star imports are by design here, not bugs.
  - `E501` — `ruff format` already owns code line width; the only lines it can't wrap are long URLs/strings, so linting E501 on top just nags.
- **Per-file:** `__init__.py` ignores `F401` — those "unused" imports *are* the package's public API surface.

If new code legitimately needs a star import or a long URL string, that's already covered. Do not add blanket `# noqa` to silence other rules — fix the code instead.

## CI gate

`.github/workflows/ci.yml` runs on PRs and pushes to `main`: ruff lint + format check, and the unit suite on Python 3.10 / 3.12 / 3.13. A PR is green when ruff is clean and `pytest tests/sdk tests/mcp` passes. Match this locally before pushing.
