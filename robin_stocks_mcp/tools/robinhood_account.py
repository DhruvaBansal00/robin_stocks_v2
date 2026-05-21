"""Robinhood account tools."""

from __future__ import annotations

from typing import Any, Optional

import robin_stocks.robinhood as rh

from ..app import mcp
from ..runtime import safe_tool, to_thread


@mcp.tool()
@safe_tool()
async def rh_load_phoenix_account(info: Optional[str] = None) -> Any:
    """Return unified information about your Robinhood account (cash, equity, buying power)."""
    return await to_thread(rh.load_phoenix_account, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_historical_portfolio(
    interval: Optional[str] = None,
    span: str = "week",
    bounds: str = "regular",
    info: Optional[str] = None,
) -> Any:
    """Get historical portfolio value over time.

    interval: one of 5minute / 10minute / hour / day / week
    span:     one of day / week / month / 3month / year / 5year / all
    bounds:   regular / extended / trading / 24_7
    """
    return await to_thread(
        rh.get_historical_portfolio, interval=interval, span=span, bounds=bounds, info=info
    )


@mcp.tool()
@safe_tool()
async def rh_get_all_positions(info: Optional[str] = None) -> Any:
    """Return a list containing every position ever traded."""
    return await to_thread(rh.get_all_positions, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_open_stock_positions(
    account_number: Optional[str] = None, info: Optional[str] = None
) -> Any:
    """Return a list of stocks that are currently held."""
    return await to_thread(rh.get_open_stock_positions, account_number=account_number, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_dividends(info: Optional[str] = None) -> Any:
    """Return a list of dividend transactions with rate, amount, shares, and date paid."""
    return await to_thread(rh.get_dividends, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_total_dividends() -> Any:
    """Return the total amount of dividends paid to the account."""
    return await to_thread(rh.get_total_dividends)


@mcp.tool()
@safe_tool()
async def rh_get_dividends_by_instrument(instrument: str, dividend_data: list) -> Any:
    """Given an instrument URL and the result of rh_get_dividends, summarize that instrument's dividends."""
    return await to_thread(rh.get_dividends_by_instrument, instrument, dividend_data)


@mcp.tool()
@safe_tool()
async def rh_get_notifications(info: Optional[str] = None) -> Any:
    """Return a list of account notifications."""
    return await to_thread(rh.get_notifications, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_latest_notification() -> Any:
    """Return the time of the latest notification."""
    return await to_thread(rh.get_latest_notification)


@mcp.tool()
@safe_tool()
async def rh_get_wire_transfers(info: Optional[str] = None) -> Any:
    """Return a list of wire transfers."""
    return await to_thread(rh.get_wire_transfers, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_margin_calls(symbol: Optional[str] = None) -> Any:
    """Return all margin calls (or those for a specific stock)."""
    return await to_thread(rh.get_margin_calls, symbol=symbol)


@mcp.tool()
@safe_tool(write=True)
async def rh_withdrawl_funds_to_bank_account(
    ach_relationship: str, amount: float, info: Optional[str] = None
) -> Any:
    """Withdraw money from Robinhood to a linked bank account."""
    return await to_thread(rh.withdrawl_funds_to_bank_account, ach_relationship, amount, info=info)


@mcp.tool()
@safe_tool(write=True)
async def rh_deposit_funds_to_robinhood_account(
    ach_relationship: str, amount: float, info: Optional[str] = None
) -> Any:
    """Deposit money from a linked bank account to Robinhood."""
    return await to_thread(
        rh.deposit_funds_to_robinhood_account, ach_relationship, amount, info=info
    )


@mcp.tool()
@safe_tool()
async def rh_get_linked_bank_accounts(info: Optional[str] = None) -> Any:
    """Return all linked bank accounts."""
    return await to_thread(rh.get_linked_bank_accounts, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_bank_account_info(id: str, info: Optional[str] = None) -> Any:
    """Return info for a single linked bank account by id."""
    return await to_thread(rh.get_bank_account_info, id, info=info)


@mcp.tool()
@safe_tool(write=True)
async def rh_unlink_bank_account(id: str) -> Any:
    """Unlink a bank account by id."""
    return await to_thread(rh.unlink_bank_account, id)


@mcp.tool()
@safe_tool()
async def rh_get_bank_transfers(
    direction: Optional[str] = None, info: Optional[str] = None
) -> Any:
    """Return all bank transfers made for the account. `direction` filters deposit/withdraw."""
    return await to_thread(rh.get_bank_transfers, direction=direction, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_card_transactions(
    cardType: Optional[str] = None, info: Optional[str] = None
) -> Any:
    """Return all debit card transactions made on the account."""
    return await to_thread(rh.get_card_transactions, cardType=cardType, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_stock_loan_payments(info: Optional[str] = None) -> Any:
    """Return a list of stock loan payments."""
    return await to_thread(rh.get_stock_loan_payments, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_interest_payments(info: Optional[str] = None) -> Any:
    """Return a list of interest payments."""
    return await to_thread(rh.get_interest_payments, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_margin_interest(info: Optional[str] = None) -> Any:
    """Return a list of margin interest charges."""
    return await to_thread(rh.get_margin_interest, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_subscription_fees(info: Optional[str] = None) -> Any:
    """Return a list of Robinhood Gold subscription fees."""
    return await to_thread(rh.get_subscription_fees, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_referrals(info: Optional[str] = None) -> Any:
    """Return a list of referrals."""
    return await to_thread(rh.get_referrals, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_day_trades(info: Optional[str] = None) -> Any:
    """Return recent day trades."""
    return await to_thread(rh.get_day_trades, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_documents(info: Optional[str] = None) -> Any:
    """Return a list of documents released to the account."""
    return await to_thread(rh.get_documents, info=info)


@mcp.tool()
@safe_tool(write=True)
async def rh_download_document(url: str, name: Optional[str] = None, dirpath: Optional[str] = None) -> str:
    """Download a single document by URL and save it as a PDF on disk."""
    await to_thread(rh.download_document, url, name=name, dirpath=dirpath)
    return f"ok: document saved (name={name!r}, dirpath={dirpath!r})"


@mcp.tool()
@safe_tool(write=True)
async def rh_download_all_documents(
    doctype: Optional[str] = None, dirpath: Optional[str] = None
) -> str:
    """Download all documents associated with the account as PDFs."""
    await to_thread(rh.download_all_documents, doctype=doctype, dirpath=dirpath)
    return f"ok: documents saved (doctype={doctype!r}, dirpath={dirpath!r})"


@mcp.tool()
@safe_tool()
async def rh_get_all_watchlists(info: Optional[str] = None) -> Any:
    """Return a list of all watchlists that have been created."""
    return await to_thread(rh.get_all_watchlists, info=info)


@mcp.tool()
@safe_tool()
async def rh_get_watchlist_by_name(
    name: str = "My First List", info: Optional[str] = None
) -> Any:
    """Return the stocks in a single watchlist."""
    return await to_thread(rh.get_watchlist_by_name, name=name, info=info)


@mcp.tool()
@safe_tool(write=True)
async def rh_post_symbols_to_watchlist(
    inputSymbols: list[str], name: str = "My First List"
) -> Any:
    """Add stock tickers to a watchlist."""
    return await to_thread(rh.post_symbols_to_watchlist, inputSymbols, name=name)


@mcp.tool()
@safe_tool(write=True)
async def rh_delete_symbols_from_watchlist(
    inputSymbols: list[str], name: str = "My First List"
) -> Any:
    """Delete stock tickers from a watchlist."""
    return await to_thread(rh.delete_symbols_from_watchlist, inputSymbols, name=name)


@mcp.tool()
@safe_tool()
async def rh_build_holdings(with_dividends: bool = False) -> Any:
    """Build a dictionary of important info regarding the stocks/positions the user owns."""
    return await to_thread(rh.build_holdings, with_dividends=with_dividends)


@mcp.tool()
@safe_tool()
async def rh_build_user_profile(account_number: Optional[str] = None) -> Any:
    """Build a dictionary summarizing the user account (cash, equity, dividends)."""
    return await to_thread(rh.build_user_profile, account_number=account_number)
