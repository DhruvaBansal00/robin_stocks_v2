.. image:: docs/source/_static/pics/title.PNG

Robin-Stocks API Library
========================
This library provides a pure Python interface that interacts with the Robinhood API, Gemini API,
and TD Ameritrade API. The code is simple to use, easy to understand, and easy to modify.
With this library, you can view information on stocks, options, and crypto-currencies in real-time,
create your own robo-investor or trading algorithm, and improve your programming skills.

To join our Slack channel where you can discuss trading and coding, click the link https://join.slack.com/t/robin-stocks/shared_invite/zt-7up2htza-wNSil5YDa3zrAglFFSxRIA

Supported APIs
==============
The supported APIs are Robinhood, Gemini, and TD Ameritrade. For more information about how to use the different APIs, visit the README
documents for `Robinhood Documentation`_, `Gemini Documentation`_, and `TDA Documentation`_.

Below are examples of how to call each of those modules.

>>> import robin_stocks.robinhood as rh
>>> import robin_stocks.gemini as gem
>>> import robin_stocks.tda as tda
>>> # Here are some example calls
>>> gem.get_pubticker("btcusd") # gets ticker information for Bitcoin from Gemini
>>> rh.get_all_open_crypto_orders() # gets all cypto orders from Robinhood
>>> tda.get_price_history("tsla") # get price history from TD Ameritrade

Contributing
============
If you would like to contribute to this project, follow our contributing guidelines `Here <https://github.com/jmfernandes/robin_stocks/blob/master/contributing.md>`_.

Automatic Testing
^^^^^^^^^^^^^^^^^

If you are contributing to this project and would like to use automatic testing for your changes, you will need to install pytest and pytest-dotenv. To do this type into terminal or command prompt:

>>> pip install pytest
>>> pip install pytest-dotenv

You will also need to fill out all the fields in .test.env. I recommend that you rename the file as .env once you are done adding in all your personal information. After that, you can simply run:

>>> pytest

to run all the tests. If you would like to run specific tests or run all the tests in a specific class then type:

>>> pytest tests/test_robinhood.py -k test_name_apple # runs only the 1 test
>>> pytest tests/test_gemini.py -k TestTrades # runs every test in TestTrades but nothing else

Finally, if you would like the API calls to print out to terminal, then add the -s flag to any of the above pytest calls.


Installing
========================
There is no need to download these files directly. This project is published on PyPi,
so it can be installed by typing into terminal (on Mac) or into command prompt (on PC):

>>> pip install robin_stocks

Also be sure that Python 3 is installed. If you need to install python you can download it from `Python.org <https://www.python.org/downloads/>`_.
Pip is the package installer for python, and is automatically installed when you install python. To learn more about Pip, you can go to `PyPi.org <https://pypi.org/project/pip/>`_.

If you would like to be able to make changes to the package yourself, clone the repository onto your computer by typing into the terminal or command prompt:

>>> git clone https://github.com/jmfernandes/robin_stocks.git
>>> cd robin_stocks

Now that you have cd into the repository you can type

>>> pip install .

and this will install whatever you changed in the local files. This will allow you to make changes and experiment with your own code.

List of Functions and Example Usage
===================================

For a complete list of all Robinhood API functions and what the different parameters mean,
go to `readthedocs.io Robinhood Page <https://robin-stocks.readthedocs.io/en/latest/robinhood.html>`_. If you would like to
see some example code and instructions on how to set up two-factor authorization for Robinhood,
go to the `Robinhood Documentation`_.

For a complete list of all TD Ameritrade API functions and what the different parameters mean,
go to `readthedocs.io TDA Page <https://robin-stocks.readthedocs.io/en/latest/tda.html>`_. For detailed instructions on
how to generate API keys for TD Ameritrade and how to use the API, go to the `TDA Documentation`_.

For a complete list of all Gemini API functions and what the different parameters mean,
go to `readthedocs.io Gemini Page <https://robin-stocks.readthedocs.io/en/latest/gemini.html>`_. For detailed instructions on
how to generate API keys for Gemini and how to use both the private and public API, go to the `Gemini Documentation`_.

MCP Server
==========
This repo also ships an `MCP <https://modelcontextprotocol.io>`_ server that exposes
the entire ``robin_stocks`` SDK (Robinhood, TD Ameritrade, Gemini) as **188 tools**
usable from any MCP client — Claude Code, Claude Desktop, Continue, Cursor, custom
agents, etc.

Highlights
^^^^^^^^^^

- 188 tools — 143 Robinhood, 20 TDA, 25 Gemini — prefixed ``rh_*`` / ``tda_*`` / ``gem_*``.
- **Read-only by default.** Order placement, cancellation, money transfers, watchlist
  mutations, and file exports return a structured ``ReadOnlyError`` until you
  explicitly set ``ROBIN_STOCKS_MCP_READ_ONLY=false``.
- Auto-login from environment variables at startup. TOTP secrets in
  ``ROBINHOOD_MFA_CODE`` are expanded to the current 6-digit code automatically.
- Blocking SDK calls are offloaded to a thread pool so the MCP event loop stays
  responsive.
- Every tool catches exceptions and returns ``{"error": True, "type", "message"}``
  payloads instead of crashing the transport.

Install
^^^^^^^

From a clone of this repo::

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[mcp]"

That installs the bundled local ``robin_stocks`` SDK plus the new
``robin_stocks_mcp`` package and the ``mcp[cli]`` runtime, and registers a
``robin-stocks-mcp`` console script.

First-time setup (interactive — one time only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MCP server leans on the SDK's own credential persistence — there is no
plaintext ``.env`` involved by default. Run the appropriate setup command for
each broker you want, then forget about it::

    robin-stocks-mcp login        # Robinhood — writes ~/.tokens/robinhood.pickle
    robin-stocks-mcp tda-setup    # TDA — encrypts client_id + tokens to disk

The Robinhood pickle is reused on every later run; no username/password is
required again until the token expires. TDA needs the encryption passcode you
chose during ``tda-setup`` to unlock the credential store — pass it via the
``tda_login`` MCP tool or set ``TDA_ENCRYPTION_PASSCODE`` in the environment.

Gemini's SDK has no on-disk persistence, so you must provide API keys either
via the ``gem_login`` MCP tool or via ``GEMINI_API_KEY`` / ``GEMINI_SECRET_KEY``.

Run locally
^^^^^^^^^^^

::

    robin-stocks-mcp                                # stdio (the implicit `serve`)
    robin-stocks-mcp serve --transport stdio        # explicit form
    robin-stocks-mcp serve --transport sse
    robin-stocks-mcp serve --transport streamable-http

Connect from Claude Code
^^^^^^^^^^^^^^^^^^^^^^^^

After you have run ``robin-stocks-mcp login`` once, wiring it into Claude Code
is a one-liner — no credentials in the command::

    claude mcp add robin-stocks "$PWD/.venv/bin/robin-stocks-mcp"

Add ``--scope user`` to make the server available across every Claude Code
project on this machine, or ``--scope project`` to commit a ``.mcp.json`` to
the repo so teammates pick it up. To allow order placement, append
``--env ROBIN_STOCKS_MCP_READ_ONLY=false`` (default is read-only).

Verify it loaded::

    claude mcp list

In a Claude Code session you can also type ``/mcp`` to see live status, or
just ask "what robin-stocks tools do you have?".

Connect from Claude Desktop
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add an entry to your Claude Desktop config
(``~/Library/Application Support/Claude/claude_desktop_config.json`` on macOS,
``%APPDATA%\Claude\claude_desktop_config.json`` on Windows), replace the path
with your checkout, and restart Claude Desktop::

    {
      "mcpServers": {
        "robin-stocks": {
          "command": "/ABSOLUTE/PATH/TO/robin_stocks-mcp/.venv/bin/robin-stocks-mcp",
          "args": ["serve", "--transport", "stdio"],
          "env": { "ROBIN_STOCKS_MCP_READ_ONLY": "true" }
        }
      }
    }

No credentials in the config — the server reads the pickle that
``robin-stocks-mcp login`` wrote. To allow order placement, change the
``ROBIN_STOCKS_MCP_READ_ONLY`` value to ``"false"``.

Non-interactive setups (CI, containers)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you cannot run the interactive setup commands, create a ``.env`` file in
the repo root (loaded automatically via ``python-dotenv``) and set whichever
of the following apply:

=================================  ===========================================
Variable                           Purpose
=================================  ===========================================
``ROBIN_STOCKS_MCP_READ_ONLY``     ``true`` (default) blocks all write tools.
``ROBIN_STOCKS_MCP_AUTO_LOGIN``    ``true`` (default) enables startup login.
``ROBINHOOD_USERNAME``             Used only if ``~/.tokens/robinhood.pickle``
                                   is missing or invalid.
``ROBINHOOD_PASSWORD``             Same.
``ROBINHOOD_MFA_CODE``             6-digit code OR a base32 TOTP secret
                                   (auto-expanded).
``TDA_ENCRYPTION_PASSCODE``        Passcode that unlocks the encrypted TDA
                                   credential store.
``GEMINI_API_KEY``                 Gemini API key.
``GEMINI_SECRET_KEY``              Gemini API secret.
``GEMINI_SANDBOX``                 ``true`` to point the SDK at Gemini's
                                   sandbox.
=================================  ===========================================

Don't reuse ``.test.env`` for this — that file is specifically for upstream's
pytest fixtures and uses different (lowercase) keys.

Tool surface (sample)
^^^^^^^^^^^^^^^^^^^^^

================================================  ===============================================
Tool                                              What it does
================================================  ===============================================
``rh_login`` / ``rh_logout``                      Robinhood auth
``rh_get_quotes``                                 Quote info for tickers
``rh_get_latest_price``                           Latest price string per ticker
``rh_get_stock_historicals``                      OHLC bars
``rh_build_holdings``                             Full portfolio summary
``rh_get_open_option_positions``                  Open option positions
``rh_find_tradable_options``                      Search the option chain
``rh_get_crypto_quote``                           Crypto quote
``rh_order_buy_market`` *(write)*                 Market buy
``rh_order_buy_limit`` *(write)*                  Limit buy
``rh_cancel_stock_order`` *(write)*               Cancel a specific stock order
``tda_get_accounts``                              List TDA accounts
``tda_get_price_history``                         Historical bars from TDA
``tda_get_option_chains``                         TDA option chain
``tda_place_order`` *(write)*                     Place a TDA order
``gem_get_pubticker``                             Gemini public ticker
``gem_check_available_balances``                  Gemini account balances
``gem_order`` / ``gem_order_market`` *(write)*    Place a Gemini order
================================================  ===============================================

Tools marked *(write)* are blocked when ``ROBIN_STOCKS_MCP_READ_ONLY=true``.

Architecture
^^^^^^^^^^^^

::

    robin_stocks_mcp/
      app.py            shared FastMCP instance
      server.py         CLI / startup
      config.py         env-driven config
      runtime.py        @safe_tool decorator, read-only guard, thread offload
      auth.py           startup login bootstrap
      tools/
        robinhood_*.py  9 modules
        tda_*.py        5 modules
        gemini_*.py     4 modules

Each tool is a thin async wrapper. ``@safe_tool`` blocks writes in read-only
mode, catches exceptions, and awaits the wrapped coroutine. ``to_thread``
runs the blocking ``requests``-based SDK call off the event loop.

Testing
^^^^^^^

::

    pip install -e ".[mcp,dev]"
    pytest tests/mcp -q

73 tests cover the runtime helpers, env-var parsing, the auth bootstrap, every
tool module (registration + dispatch + write-guard + exception capture via
``unittest.mock``), and a subprocess that boots the real server over STDIO,
completes the MCP handshake, lists tools, and verifies the write guard.

Safety notes
^^^^^^^^^^^^

- Read-only is the default for a reason. Confirm a tool's behaviour on
  paper-money / sandbox first if your broker supports it
  (``GEMINI_SANDBOX=true``).
- Sessions are persisted via pickle under ``~/.tokens/`` by default. Treat
  that directory like credentials.
- The MCP server speaks plaintext JSON-RPC over STDIO. Do not run it across a
  network without a transport you trust.

.. _Robinhood Documentation: Robinhood.rst
.. _Gemini Documentation: gemini.rst
.. _TDA Documentation: tda.rst
