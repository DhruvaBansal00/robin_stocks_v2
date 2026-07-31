"""Contains functions for browsing and trading prediction-market event contracts.

Event contracts trade on Robinhood's derivatives (Ceres) backend and require the
same ``Rh-Contract-Protected`` session header as futures. Browsing uses the
``prediction-markets`` service; orders, positions, and accounts use ``ceres``.

The ``YES``/``NO`` outcome of a market is encoded by the ``contract_id`` you trade
(each outcome is its own contract). ``side`` is ``"BUY"`` to open and ``"SELL"`` to
close a position on that contract.
"""

from uuid import uuid4

from robin_stocks.robinhood.helper import (
    filter_data,
    get_output,
    login_required,
    request_get,
    request_post,
    update_session_for_futures,
)
from robin_stocks.robinhood.urls import (
    event_contract_cancel_url,
    event_contract_fees_url,
    event_contract_orders_url,
    event_contract_positions_url,
    event_contract_url,
    futures_account_url,
    futures_orders_url,
    prediction_markets_event_url,
    prediction_markets_events_url,
    prediction_markets_layout_url,
    prediction_markets_navigation_url,
)

# Browse Functions


@login_required
def get_prediction_market_categories(info=None):
    """Get the list of prediction-market categories (navigation nodes).

    :param info: Will filter the results to get a specific value
    :type info: Optional[str]
    :returns: List of category nodes. Each has ``id`` and ``displayHeaderText`` \
    (e.g. 'Crypto', 'Soccer', 'Politics'); the display name is what you pass to \
    :func:`get_prediction_market_events`.

    """
    update_session_for_futures()
    data = request_get(prediction_markets_navigation_url())

    if data and "nodes" in data:
        return filter_data(data["nodes"], info)
    return None


@login_required
def get_prediction_market_events(category, info=None):
    """Get prediction-market events for a category.

    :param category: Category display name (e.g. 'Crypto', 'Soccer', 'Politics'). \
    See :func:`get_prediction_market_categories`.
    :type category: str
    :param info: Will filter the results to get a specific value
    :type info: Optional[str]
    :returns: List of event dictionaries. Each event has an ``eventContracts`` map \
    keyed by outcome, where each contract has an ``id`` you trade.

    """
    update_session_for_futures()
    data = request_get(prediction_markets_events_url(), payload={"categories": category})

    if data and "results" in data:
        return filter_data(data["results"], info)
    return None


@login_required
def get_prediction_market_node_id(category):
    """Resolve a category display name to its navigation node ID.

    :param category: Category display name (e.g. 'Pro basketball', 'Featured', 'Sports')
    :type category: str
    :returns: The node ID string, or None if not found

    """
    nodes = get_prediction_market_categories()
    if nodes:
        for node in nodes:
            if category in (node.get("displayHeaderText"), node.get("displayTabText")):
                return node.get("id")
    return None


@login_required
def get_prediction_markets(category, info=None):
    """Get the markets shown under a category, the way the app's Prediction Markets hub displays them.

    This is the robust way to list markets for any tab (including ones the
    ``categories`` filter on :func:`get_prediction_market_events` rejects, such as
    'Pro basketball'), and it surfaces live in-game markets.

    :param category: Category display name (e.g. 'Pro basketball') or a navigation node ID
    :type category: str
    :param info: Will filter the results to get a specific value
    :type info: Optional[str]
    :returns: List of layout components. Each ``eventComponent`` carries an ``eventId`` \
    and ``contractInfo`` (``contractId``, ``shortName``, ``longName``, ``tradability``).

    """
    node_id = category if "-" in category and " " not in category else get_prediction_market_node_id(category)
    if not node_id:
        print(f"Could not resolve category '{category}' to a node.", file=get_output())
        return None

    update_session_for_futures()
    data = request_get(prediction_markets_layout_url(), payload={"node_id": node_id})

    if data and isinstance(data.get("results"), dict):
        return filter_data(data["results"].get("components", []), info)
    return None


@login_required
def get_prediction_market_event(event_id, info=None):
    """Get details for a single prediction-market event.

    :param event_id: The event ID
    :type event_id: str
    :param info: Will filter the results to get a specific value
    :type info: Optional[str]
    :returns: Dictionary with event details, including its ``eventContracts``.

    """
    update_session_for_futures()
    data = request_get(prediction_markets_event_url(event_id))

    if data and "results" in data:
        return filter_data(data["results"], info)
    return filter_data(data, info)


@login_required
def get_event_contract(contract_id, info=None):
    """Get details for a single event contract.

    :param contract_id: The event contract ID
    :type contract_id: str
    :param info: Will filter the results to get a specific value
    :type info: Optional[str]
    :returns: Dictionary with contract details (symbol, tradability, tick sizes, etc.).

    """
    update_session_for_futures()
    data = request_get(event_contract_url(contract_id))

    if data and "eventContract" in data:
        return filter_data(data["eventContract"], info)
    return filter_data(data, info)


# Account / Position / Order Read Functions


@login_required
def get_event_contracts_account_id():
    """Get the derivatives account ID used for event contracts.

    Event contracts settle on the account with ``accountType == 'SWAP'``.

    :returns: Account ID string or None

    """
    update_session_for_futures()
    data = request_get(futures_account_url(), dataType="results")

    if data:
        for account in data:
            if isinstance(account, dict) and account.get("accountType") == "SWAP":
                return account.get("id")
    return None


@login_required
def get_event_contract_positions(account_id=None, info=None):
    """Get current event-contract positions.

    :param account_id: Derivatives account ID (auto-detected if None)
    :type account_id: Optional[str]
    :param info: Will filter the results to get a specific value
    :type info: Optional[str]
    :returns: List of position dictionaries

    """
    if account_id is None:
        account_id = get_event_contracts_account_id()
        if account_id is None:
            print("Error: could not find a SWAP (event-contracts) account.", file=get_output())
            return None

    update_session_for_futures()
    data = request_get(event_contract_positions_url(account_id), dataType="results")
    return filter_data(data, info)


@login_required
def get_event_contract_orders(account_id=None, info=None):
    """Get event-contract orders with automatic pagination.

    :param account_id: Derivatives account ID (auto-detected if None)
    :type account_id: Optional[str]
    :param info: Will filter the results to get a specific value
    :type info: Optional[str]
    :returns: List of order dictionaries

    """
    if account_id is None:
        account_id = get_event_contracts_account_id()
        if account_id is None:
            print("Error: could not find a SWAP (event-contracts) account.", file=get_output())
            return None

    update_session_for_futures()

    all_orders = []
    cursor = None
    page = 1
    while True:
        payload = {"cursor": cursor} if cursor else None
        data = request_get(futures_orders_url(account_id), payload=payload)

        if not data or "results" not in data:
            break

        all_orders.extend(data["results"])

        cursor = data.get("next")
        if not cursor:
            break

        print(f"Loading page {page + 1} ...", file=get_output())
        page += 1

    return filter_data(all_orders, info)


@login_required
def get_event_contract_order_info(order_id, account_id=None, info=None):
    """Get details for a specific event-contract order.

    :param order_id: The event-contract order ID
    :type order_id: str
    :param account_id: Derivatives account ID (auto-detected if None)
    :type account_id: Optional[str]
    :param info: Will filter the results to get a specific value
    :type info: Optional[str]
    :returns: Dictionary with order details, or None if not found

    """
    all_orders = get_event_contract_orders(account_id, info=None)
    if not all_orders:
        return None

    for order in all_orders:
        if order.get("orderId") == order_id or order.get("id") == order_id:
            return filter_data(order, info)
    return None


# Order Preview / Placement Functions


def _build_leg(contract_id, side):
    """Build a single event-contract order leg.

    :param contract_id: The event contract ID
    :type contract_id: str
    :param side: 'BUY' to open or 'SELL' to close
    :type side: str
    :returns: Leg dictionary

    """
    return {
        "contract_id": contract_id,
        "order_side": side.upper(),
        "ratio_quantity": 1,
        "contract_type": "EVENT_CONTRACT",
    }


@login_required
def get_event_contract_order_fees(contract_id, side, quantity, limit_price, account_id=None, info=None):
    """Preview the fees for an event-contract order without placing it.

    :param contract_id: The event contract ID
    :type contract_id: str
    :param side: 'BUY' to open or 'SELL' to close
    :type side: str
    :param quantity: Number of contracts
    :type quantity: str or float or int
    :param limit_price: Limit price per contract (0.01 - 0.99)
    :type limit_price: str or float
    :param account_id: Derivatives account ID (auto-detected if None)
    :type account_id: Optional[str]
    :param info: Will filter the results to get a specific value
    :type info: Optional[str]
    :returns: Dictionary with fee breakdown (totalFee, totalCommission, etc.)

    """
    if account_id is None:
        account_id = get_event_contracts_account_id()
        if account_id is None:
            print("Error: could not find a SWAP (event-contracts) account.", file=get_output())
            return None

    payload = {
        "account_id": account_id,
        "tentative_futures_order": {
            "legs": [_build_leg(contract_id, side)],
            "limit_price": str(limit_price),
            "order_type": "LIMIT",
            "quantity": str(quantity),
        },
    }

    update_session_for_futures()
    data = request_post(event_contract_fees_url(), payload=payload, json=True)
    return filter_data(data, info)


@login_required
def order_event_contract(
    contract_id,
    side,
    quantity,
    limit_price,
    client_marketdata,
    quote_id,
    account_id=None,
    time_in_force="GTC",
    ref_id=None,
    info=None,
):
    """Place an event-contract (prediction-market) order.

    .. warning::
        The Robinhood server validates ``client_marketdata`` against its live order
        book and requires a ``quote_id`` issued for the current quote, so an order
        cannot be placed from stale or fabricated prices. Robinhood streams event-
        contract quotes over a websocket / combo-RFQ channel that this SDK does not
        yet implement, so you must obtain ``client_marketdata`` and ``quote_id`` from
        a live quote yourself. This function builds and submits the request faithfully
        but has only been validated structurally (see :func:`get_event_contract_order_fees`
        for a no-quote fee preview).

    :param contract_id: The event contract ID (encodes the YES/NO outcome)
    :type contract_id: str
    :param side: 'BUY' to open a position or 'SELL' to close one
    :type side: str
    :param quantity: Number of contracts
    :type quantity: str or float or int
    :param limit_price: Limit price per contract (0.01 - 0.99)
    :type limit_price: str or float
    :param client_marketdata: Live quote snapshot. Shape: \
    ``{"bid": {"value": "0.44"}, "ask": {"value": "0.45"}, "marketable": bool, \
    "platform": "api", "timestamp": {"value": "2026-05-23T17:00:00Z"}}``.
    :type client_marketdata: dict
    :param quote_id: Quote ID issued by Robinhood for the current quote.
    :type quote_id: str
    :param account_id: Derivatives account ID (auto-detected if None)
    :type account_id: Optional[str]
    :param time_in_force: One of 'GTC', 'IOC', 'FOK', 'GFD', 'GTD'
    :type time_in_force: str
    :param ref_id: Client-generated idempotency UUID (auto-generated if None)
    :type ref_id: Optional[str]
    :param info: Will filter the results to get a specific value
    :type info: Optional[str]
    :returns: Dictionary with the created order

    """
    if account_id is None:
        account_id = get_event_contracts_account_id()
        if account_id is None:
            print("Error: could not find a SWAP (event-contracts) account.", file=get_output())
            return None

    payload = {
        "account_id": account_id,
        "legs": [_build_leg(contract_id, side)],
        "quantity": str(quantity),
        "limit_price": str(limit_price),
        "time_in_force": time_in_force.upper(),
        "ref_id": ref_id or str(uuid4()),
        "quote_id": quote_id,
        "client_marketdata": client_marketdata,
    }

    update_session_for_futures()
    data = request_post(event_contract_orders_url(), payload=payload, json=True)
    return filter_data(data, info)


@login_required
def cancel_event_contract_order(order_id, info=None):
    """Cancel an event-contract order.

    :param order_id: The event-contract order ID
    :type order_id: str
    :param info: Will filter the results to get a specific value
    :type info: Optional[str]
    :returns: Dictionary with the cancellation response

    """
    update_session_for_futures()
    data = request_post(event_contract_cancel_url(order_id), json=True)
    return filter_data(data, info)
