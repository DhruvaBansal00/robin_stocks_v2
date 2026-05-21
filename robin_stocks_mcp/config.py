"""Environment-driven configuration for the robin_stocks MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


def _bool_env(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Config:
    # Global behaviour
    read_only: bool = True  # Default safe: refuse order/transfer/cancel tools
    auto_login: bool = True

    # Robinhood
    rh_username: Optional[str] = None
    rh_password: Optional[str] = None
    rh_mfa_code: Optional[str] = None  # TOTP secret OR static code
    rh_pickle_path: Optional[str] = None
    rh_pickle_name: Optional[str] = None

    # TD Ameritrade
    tda_encryption_passcode: Optional[str] = None

    # Gemini
    gemini_api_key: Optional[str] = None
    gemini_secret_key: Optional[str] = None
    gemini_sandbox: bool = False


def load_config() -> Config:
    return Config(
        read_only=_bool_env("ROBIN_STOCKS_MCP_READ_ONLY", default=True),
        auto_login=_bool_env("ROBIN_STOCKS_MCP_AUTO_LOGIN", default=True),
        rh_username=os.getenv("ROBINHOOD_USERNAME") or os.getenv("RH_USERNAME"),
        rh_password=os.getenv("ROBINHOOD_PASSWORD") or os.getenv("RH_PASSWORD"),
        rh_mfa_code=os.getenv("ROBINHOOD_MFA_CODE") or os.getenv("RH_MFA_CODE"),
        rh_pickle_path=os.getenv("ROBINHOOD_PICKLE_PATH"),
        rh_pickle_name=os.getenv("ROBINHOOD_PICKLE_NAME"),
        tda_encryption_passcode=os.getenv("TDA_ENCRYPTION_PASSCODE"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        gemini_secret_key=os.getenv("GEMINI_SECRET_KEY"),
        gemini_sandbox=_bool_env("GEMINI_SANDBOX", default=False),
    )
