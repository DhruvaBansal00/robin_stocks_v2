"""Contains functions for getting IPO Access information.

IPO Access is Robinhood's retail allocation program: when a company goes public
through an underwriter Robinhood works with, eligible customers can request
shares at the offering price before the stock starts trading.

The endpoints behind it are undocumented view models served by
bonfire.robinhood.com. Their paths were read out of the web app bundle
(cdn.robinhood.com/assets/generated_assets/webapp/App-*.js) and verified against
a live authenticated session.

These functions are read-only. Requesting shares is not wrapped here: an IPO
Access order is an ordinary equity order carrying `is_ipo_access_order`, and the
submission payload could not be verified without a live offering — see
get_ipo_access_orders() for reading the ones you have placed.
"""

from robin_stocks.robinhood.helper import *
from robin_stocks.robinhood.orders import get_all_stock_orders
from robin_stocks.robinhood.urls import *


@login_required
def get_ipo_access_list(info=None):
    """Returns the IPO Access list view model — the offerings available to your account.

    When Robinhood has no IPOs on offer, the response carries an 'empty_state'
    section instead of any offering, which is what an account with no available
    IPOs sees in the app.

    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a dictionary of key/value pairs for the list view model. If info parameter is provided, \
    the value of the key that matches info is returned.
    :Dictionary Keys: * empty_state
                      * learn_tab

    """
    url = ipo_access_list_url()
    data = request_get(url)

    return filter_data(data, info)


@login_required
def get_ipo_access_cards(instrument_ids, info=None):
    """Returns the IPO Access card for each of the given instruments.

    :param instrument_ids: The instrument id, or a list of instrument ids, to look up.
    :type instrument_ids: str or list
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a list of dictionaries of key/value pairs for each card. If info parameter is provided, \
    a list of strings is returned where the strings are the value of the key that matches info.

    """
    url = ipo_access_cards_url(instrument_ids)
    data = request_get(url, "results")

    return filter_data(data, info)


@login_required
def get_ipo_access_summary(instrument_id, info=None):
    """Returns the summary view model for an IPO — the company, its dates, and its price range.

    :param instrument_id: The instrument id of the company going public.
    :type instrument_id: str
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a dictionary of key/value pairs for the summary. If info parameter is provided, \
    the value of the key that matches info is returned.

    """
    url = ipo_access_summary_url(instrument_id)
    data = request_get(url)

    return filter_data(data, info)


@login_required
def get_ipo_access_order_entry(instrument_id, account_number=None, info=None):
    """Returns the order-entry view model for an IPO: its quote, the deal phase, and your eligibility.

    This is what tells you whether you can actually request shares — 'context'
    carries user_is_eligible, user_is_enrolled, has_cob_deadline_passed, your
    available buying power, and the ipo_access_quote price range.

    :param instrument_id: The instrument id of the company going public.
    :type instrument_id: str
    :param account_number: The account number to price the order against.
    :type account_number: Optional[str]
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a dictionary of key/value pairs for the order entry view model. If info parameter is \
    provided, the value of the key that matches info is returned.
    :Dictionary Keys: * account_number
                      * context
                      * form_state
                      * instrument_id
                      * ipoa_new_orders_blocked_details
                      * order_entry_view_model
                      * trade_receipt_view_model

    """
    url = ipo_access_order_entry_url(instrument_id, account_number)
    data = request_get(url)

    return filter_data(data, info)


@login_required
def get_ipo_access_allocation_results(instrument_id, info=None):
    """Returns how many shares you were allocated in an IPO you requested shares in.

    :param instrument_id: The instrument id of the company that went public.
    :type instrument_id: str
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a dictionary of key/value pairs for the allocation results. If info parameter is provided, \
    the value of the key that matches info is returned.

    """
    url = ipo_access_allocation_results_url(instrument_id)
    data = request_get(url)

    return filter_data(data, info)


@login_required
def get_ipo_access_trade_receipt(order_id, info=None):
    """Returns the trade receipt for a filled IPO Access order.

    :param order_id: The id of the IPO Access order.
    :type order_id: str
    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :returns: Returns a dictionary of key/value pairs for the receipt. If info parameter is provided, \
    the value of the key that matches info is returned.

    """
    url = ipo_access_trade_receipt_url(order_id)
    data = request_get(url)

    return filter_data(data, info)


@login_required
def get_ipo_access_orders(info=None, account_number=None, start_date=None):
    """Returns the stock orders you placed through IPO Access.

    IPO Access orders live alongside ordinary equity orders and are flagged with
    'is_ipo_access_order', so this filters the regular order history down to them.

    :param info: Will filter the results to get a specific value.
    :type info: Optional[str]
    :param account_number: The account number to read orders for.
    :type account_number: Optional[str]
    :param start_date: Sets the date of when to start returning orders.
    :type start_date: Optional[str]
    :returns: Returns a list of dictionaries of key/value pairs for each IPO Access order. If info parameter \
    is provided, a list of strings is returned where the strings are the value of the key that matches info.

    """
    orders = get_all_stock_orders(account_number=account_number, start_date=start_date)
    ipo_orders = [order for order in orders if order and order.get("is_ipo_access_order")]

    return filter_data(ipo_orders, info)
