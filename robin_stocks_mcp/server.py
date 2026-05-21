"""Entry point for the robin_stocks MCP server."""

from __future__ import annotations

import argparse
import getpass
import sys

import robin_stocks.gemini as gem
import robin_stocks.robinhood as rh
import robin_stocks.tda as tda

from .app import mcp
from .auth import bootstrap_login
from .config import load_config
from .runtime import set_config


def _register_all_tools() -> None:
    # Importing each module registers its tools on the shared `mcp` instance.
    from .tools import (  # noqa: F401
        robinhood_auth,
        robinhood_account,
        robinhood_profiles,
        robinhood_stocks,
        robinhood_options,
        robinhood_crypto,
        robinhood_markets,
        robinhood_orders,
        robinhood_export,
        tda_auth,
        tda_account,
        tda_stocks,
        tda_markets,
        tda_orders,
        gemini_auth,
        gemini_account,
        gemini_crypto,
        gemini_orders,
    )


def _cmd_serve(args: argparse.Namespace) -> int:
    cfg = load_config()
    set_config(cfg)
    bootstrap_login(cfg)
    _register_all_tools()
    print(
        f"[robin_stocks_mcp] starting; transport={args.transport} "
        f"read_only={cfg.read_only} auto_login={cfg.auto_login}",
        file=sys.stderr,
    )
    mcp.run(transport=args.transport)
    return 0


def _cmd_login(args: argparse.Namespace) -> int:
    """Interactive Robinhood first-time login. Writes the session pickle to disk."""
    print("Robinhood interactive login. Credentials are not stored in plaintext —")
    print("only the resulting session token is pickled under ~/.tokens/.")
    username = args.username or input("Robinhood username: ").strip()
    password = args.password or getpass.getpass("Robinhood password: ")
    mfa = args.mfa_code  # may be None; the SDK will prompt during login if needed
    rh.login(username=username, password=password, mfa_code=mfa, store_session=True)
    print("Login complete; pickle written. Future `robin-stocks-mcp` runs will reuse it.")
    return 0


def _cmd_tda_setup(args: argparse.Namespace) -> int:
    """One-time TDA credential seeding. Stores encrypted tokens via the SDK."""
    print("TD Ameritrade first-time setup. You'll need a TDA developer-portal")
    print("client_id, an authorization_token, and a refresh_token.")
    if args.generate_passcode:
        passcode = tda.generate_encryption_passcode()
        print(f"\nGenerated encryption passcode (save this — you'll need it on every run):")
        print(f"  {passcode}\n")
    else:
        passcode = args.passcode or getpass.getpass("Encryption passcode: ")
    client_id = args.client_id or input("client_id: ").strip()
    auth_token = args.auth_token or getpass.getpass("authorization_token: ")
    refresh = args.refresh_token or getpass.getpass("refresh_token: ")
    tda.login_first_time(passcode, client_id, auth_token, refresh)
    print("TDA encrypted credentials saved. Set TDA_ENCRYPTION_PASSCODE in your")
    print("environment (or pass it via the tda_login MCP tool) to unlock them.")
    return 0


def _cmd_logout(args: argparse.Namespace) -> int:
    """Clear cached Robinhood / Gemini sessions."""
    if args.broker in ("rh", "all"):
        try:
            rh.logout()
            print("Robinhood: cleared session.")
        except Exception as e:  # noqa: BLE001
            print(f"Robinhood logout error: {e}", file=sys.stderr)
    if args.broker in ("gem", "all"):
        try:
            gem.logout()
            print("Gemini: cleared session.")
        except Exception as e:  # noqa: BLE001
            print(f"Gemini logout error: {e}", file=sys.stderr)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="robin-stocks-mcp")
    sub = parser.add_subparsers(dest="command")

    serve = sub.add_parser("serve", help="Run the MCP server (default).")
    serve.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
    )
    serve.set_defaults(func=_cmd_serve)

    login_p = sub.add_parser(
        "login", help="Interactive first-time Robinhood login (seeds the pickle)."
    )
    login_p.add_argument("--username")
    login_p.add_argument("--password")
    login_p.add_argument("--mfa-code", dest="mfa_code")
    login_p.set_defaults(func=_cmd_login)

    tda_p = sub.add_parser("tda-setup", help="One-time TDA encrypted credential setup.")
    tda_p.add_argument("--generate-passcode", action="store_true",
                       help="Generate a fresh encryption passcode and print it.")
    tda_p.add_argument("--passcode")
    tda_p.add_argument("--client-id", dest="client_id")
    tda_p.add_argument("--auth-token", dest="auth_token")
    tda_p.add_argument("--refresh-token", dest="refresh_token")
    tda_p.set_defaults(func=_cmd_tda_setup)

    logout_p = sub.add_parser("logout", help="Clear cached broker sessions.")
    logout_p.add_argument("broker", choices=["rh", "gem", "all"], default="all", nargs="?")
    logout_p.set_defaults(func=_cmd_logout)

    # Top-level `--transport` flag for backwards-compatible `robin-stocks-mcp --transport stdio`
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=None,
        help=argparse.SUPPRESS,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        # Default to `serve`, optionally honoring the legacy top-level --transport flag.
        args.command = "serve"
        args.func = _cmd_serve
        if getattr(args, "transport", None) is None:
            args.transport = "stdio"

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main() or 0)
