"""Startup login bootstrap.

Design: lean on the credential persistence each broker SDK already ships with.

- **Robinhood** stores a session JSON at ``~/.tokens/robinhood.json`` after the
  first interactive login. We reuse it directly — no creds required at startup.
  If the file is missing or expired, we surface a clear message instead of
  prompting (which would block STDIO).
- **TD Ameritrade** stores credentials encrypted with a passcode. We just need
  the passcode to unlock them; pass it via ``TDA_ENCRYPTION_PASSCODE`` or call
  the ``tda_login`` MCP tool.
- **Gemini** has no SDK-level persistence (just module globals). API keys must
  come from env or the ``gem_login`` MCP tool.

Env-var-supplied credentials remain a supported fallback for non-interactive
deployments (CI, containers), but they are not the default path.
"""

from __future__ import annotations

import json
import os
import sys

import robin_stocks.gemini as gem
import robin_stocks.robinhood as rh
import robin_stocks.tda as tda
from robin_stocks.robinhood.helper import (
    request_get,
    set_login_state,
    update_session,
)
from robin_stocks.robinhood.urls import positions_url

from .config import Config


def _log(msg: str) -> None:
    print(f"[robin_stocks_mcp] {msg}", file=sys.stderr)


def _resolve_mfa(value: str | None) -> str | None:
    """Treat the env value as either a literal MFA code or a TOTP secret."""
    if not value:
        return None
    if len(value) > 8 and all(c.isalnum() for c in value):
        try:
            import pyotp

            return pyotp.TOTP(value).now()
        except Exception:
            pass
    return value


def _robinhood_pickle_path(cfg: Config) -> str:
    base = cfg.rh_pickle_path or os.path.join(os.path.expanduser("~"), ".tokens")
    name = cfg.rh_pickle_name or ""
    return os.path.join(base, f"robinhood{name}.json")


def try_reuse_robinhood_session(cfg: Config) -> bool:
    """Load the persisted Robinhood session JSON without falling back to ``input()``.

    Returns True iff the cached token is present and the server accepts it.
    """
    pickle_path = _robinhood_pickle_path(cfg)
    if not os.path.isfile(pickle_path):
        return False
    try:
        with open(pickle_path) as f:
            data = json.load(f)
        token_type = data["token_type"]
        access_token = data["access_token"]
        update_session("Authorization", f"{token_type} {access_token}")
        # Probe the API — a 200 here means the cached token still works.
        res = request_get(positions_url(), "pagination", {"nonzero": "true"}, jsonify_data=False)
        res.raise_for_status()
        set_login_state(True)
        return True
    except Exception as e:  # noqa: BLE001
        set_login_state(False)
        update_session("Authorization", None)
        _log(f"Robinhood cached session not usable ({e!s}); ignoring.")
        return False


def bootstrap_login(cfg: Config) -> None:
    """Attempt zero-prompt login for every broker.

    Order of preference for each broker:
      1. Re-use SDK-persisted credentials if available.
      2. Fall back to env-supplied credentials.
      3. Otherwise, leave unauthenticated and tell the user to log in interactively.
    """
    if not cfg.auto_login:
        _log("auto-login disabled; skipping.")
        return

    # ---- Robinhood ----------------------------------------------------------
    try:
        rh_session_reused = try_reuse_robinhood_session(cfg)
    except Exception as e:  # noqa: BLE001 - defense in depth
        _log(f"Robinhood session-reuse threw unexpectedly ({e!s}); ignoring.")
        rh_session_reused = False
    if rh_session_reused:
        _log(f"Robinhood: reusing persisted session from {_robinhood_pickle_path(cfg)}.")
    elif cfg.rh_username and cfg.rh_password:
        try:
            rh.login(
                username=cfg.rh_username,
                password=cfg.rh_password,
                mfa_code=_resolve_mfa(cfg.rh_mfa_code),
                store_session=True,
                pickle_path=cfg.rh_pickle_path or "",
                pickle_name=cfg.rh_pickle_name or "",
            )
            _log("Robinhood: logged in with env-supplied credentials; session stored for next time.")
        except Exception as e:  # noqa: BLE001
            _log(f"Robinhood env-credential login failed: {e}")
    else:
        _log(
            "Robinhood: no cached session and no env credentials. "
            "Run `robin-stocks-mcp login` once to seed the session file, "
            "or call the `rh_login` MCP tool with username/password/mfa_code."
        )

    # ---- TD Ameritrade ------------------------------------------------------
    # TDA persists encrypted credentials; we still need the passcode to unlock.
    if cfg.tda_encryption_passcode:
        try:
            tda.login(cfg.tda_encryption_passcode)
            _log("TDA: logged in via encrypted credential store.")
        except Exception as e:  # noqa: BLE001
            _log(f"TDA login failed: {e}")
    else:
        _log(
            "TDA: no encryption passcode set. Run "
            "`robin-stocks-mcp tda-setup` once to seed encrypted credentials, "
            "or set TDA_ENCRYPTION_PASSCODE."
        )

    # ---- Gemini -------------------------------------------------------------
    # Gemini has no SDK-level persistence — API keys are required at runtime.
    if cfg.gemini_api_key and cfg.gemini_secret_key:
        try:
            if cfg.gemini_sandbox:
                gem.use_sand_box_urls(True)
            gem.login(cfg.gemini_api_key, cfg.gemini_secret_key)
            _log("Gemini: logged in with env-supplied API keys.")
        except Exception as e:  # noqa: BLE001
            _log(f"Gemini login failed: {e}")
    else:
        _log("Gemini: no API keys set. Either set GEMINI_API_KEY/GEMINI_SECRET_KEY or call the `gem_login` MCP tool.")
