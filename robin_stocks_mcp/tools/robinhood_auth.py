"""Robinhood authentication tools."""

from __future__ import annotations

from typing import Any, Optional

import robin_stocks.robinhood as rh

from ..app import mcp
from ..runtime import safe_tool, to_thread


@mcp.tool()
@safe_tool()
async def rh_login(
    username: Optional[str] = None,
    password: Optional[str] = None,
    expiresIn: int = 86400,
    scope: str = "internal",
    store_session: bool = True,
    mfa_code: Optional[str] = None,
    pickle_path: str = "",
    pickle_name: str = "",
) -> Any:
    """Log in to Robinhood. Handles MFA, session persistence, and verification workflows.

    If `mfa_code` is a base32 TOTP secret, pass the *current* code instead — this tool does not
    expand TOTP secrets (env-var auto-login does). Pickle credentials are written under
    ~/.tokens by default.
    """
    return await to_thread(
        rh.login,
        username=username,
        password=password,
        expiresIn=expiresIn,
        scope=scope,
        store_session=store_session,
        mfa_code=mfa_code,
        pickle_path=pickle_path,
        pickle_name=pickle_name,
    )


@mcp.tool()
@safe_tool()
async def rh_logout() -> str:
    """Log out of Robinhood by clearing session data."""
    await to_thread(rh.logout)
    return "ok: logged out of Robinhood"
