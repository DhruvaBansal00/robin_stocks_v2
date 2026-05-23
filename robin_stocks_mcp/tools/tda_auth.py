"""TD Ameritrade authentication tools."""

from __future__ import annotations

import robin_stocks.tda as tda

from ..app import mcp
from ..runtime import safe_tool, to_thread


@mcp.tool()
@safe_tool()
async def tda_login(encryption_passcode: str) -> str:
    """Log in to TD Ameritrade. Requires a previous `tda_login_first_time` to seed credentials."""
    await to_thread(tda.login, encryption_passcode)
    return "ok: TDA login complete"


@mcp.tool()
@safe_tool()
async def tda_login_first_time(
    encryption_passcode: str,
    client_id: str,
    authorization_token: str,
    refresh_token: str,
) -> str:
    """Persist TDA OAuth tokens encrypted on disk for future logins.

    Run once after going through the TDA developer-portal OAuth flow.
    """
    await to_thread(tda.login_first_time, encryption_passcode, client_id, authorization_token, refresh_token)
    return "ok: TDA credentials saved"


@mcp.tool()
@safe_tool()
async def tda_generate_encryption_passcode() -> str:
    """Generate a fresh encryption passcode for storing TDA credentials."""
    return await to_thread(tda.generate_encryption_passcode)
