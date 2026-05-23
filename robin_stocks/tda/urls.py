"""Module contains all the API endpoints"""

from enum import Enum, auto
from re import IGNORECASE, match, split


class AutoName(Enum):
    """Automatically sets an enum value to be its name when using auto()"""

    def _generate_next_value_(name, start, count, last_values):
        return name


class Version(AutoName):
    """Enum for different version types"""

    v1 = auto()
    v2 = auto()


class URLS:
    """Static class for holding all urls."""

    __base_url = "https://api.tdameritrade.com"

    def __init__(self):
        raise NotImplementedError(f"Cannot create instance of {self.__class__.__name__}")

    @classmethod
    def get_base_url(cls, version):
        return cls.__base_url + "/" + version.value + "/"

    @classmethod
    def get_endpoint(cls, url):
        if match(cls.__base_url, url, IGNORECASE):
            _, end = split(cls.__base_url, url, flags=IGNORECASE)
        else:
            raise ValueError("The URL has the wrong base.")

        return end

    # accounts.py
    @classmethod
    def account(cls, id):
        return cls.get_base_url(Version.v1) + f"accounts/{id}"

    @classmethod
    def accounts(cls):
        return cls.get_base_url(Version.v1) + "accounts"

    @classmethod
    def transaction(cls, id, transaction):
        return cls.get_base_url(Version.v1) + f"accounts/{id}/transactions/{transaction}"

    @classmethod
    def transactions(cls, id):
        return cls.get_base_url(Version.v1) + f"accounts/{id}/transactions"

    # authentication.py
    @classmethod
    def oauth(cls):
        return cls.get_base_url(Version.v1) + "oauth2/token"

    # markets.py
    @classmethod
    def markets(cls):
        return cls.get_base_url(Version.v1) + "marketdata/hours"

    @classmethod
    def market(cls, market):
        return cls.get_base_url(Version.v1) + f"marketdata/{market}/hours"

    @classmethod
    def movers(cls, index):
        return cls.get_base_url(Version.v1) + f"marketdata/{index}/movers"

    # orders.py
    @classmethod
    def orders(cls, account_id):
        return cls.get_base_url(Version.v1) + f"accounts/{account_id}/orders"

    @classmethod
    def order(cls, account_id, order_id):
        return cls.get_base_url(Version.v1) + f"accounts/{account_id}/orders/{order_id}"

    # stocks.py
    @classmethod
    def instruments(cls):
        return cls.get_base_url(Version.v1) + "instruments"

    @classmethod
    def instrument(cls, cusip):
        return cls.get_base_url(Version.v1) + f"instruments/{cusip}"

    @classmethod
    def quote(cls, ticker):
        return cls.get_base_url(Version.v1) + f"marketdata/{ticker}/quotes"

    @classmethod
    def quotes(cls):
        return cls.get_base_url(Version.v1) + "marketdata/quotes"

    @classmethod
    def price_history(cls, ticker):
        return cls.get_base_url(Version.v1) + f"marketdata/{ticker}/pricehistory"

    @classmethod
    def option_chains(cls):
        return cls.get_base_url(Version.v1) + "marketdata/chains"
