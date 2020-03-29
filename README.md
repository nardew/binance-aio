# binance-aio 0.0.2

**Announcement:**`binance-aio` has been replaced by a new library [`cryptolib-aio`](https://github.com/nardew/cryptolib-aio). `cryptolib-aio` offers the very same functionality as `binance-aio` but on top it provides access to multiple cryptoexchanges and other (mostly technical) new features. You can keep using `binance-aio` but please note no new features/bugfixes will be implemented. We recommend to migrate to `cryptolib-aio`.

----

[![](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-365/) [![](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-374/)

`binance-aio` is a Python library providing access to [binance crypto exchange](https://www.binance.com/en). Library implements binance's REST API as well as websockets.

`binance-aio` is designed as an asynchronous library utilizing modern features of Python and of supporting asynchronous libraries (mainly [async websockets](https://websockets.readthedocs.io/en/stable/) and [aiohttp](https://aiohttp.readthedocs.io/en/stable/)).

For changes see [CHANGELOG](https://github.com/nardew/binance-aio/blob/master/CHANGELOG.md).

### Features
- access to limited binance's REST API (account details, market data, order management, ...) and websockets (account feed, market data feed, orderbook feed, ...). Missing REST calls and websocket streams will be added on request and based on our availability.
- channels bundled in one or multiple websockets processed in parallel 
- lean architecture setting ground for the future extensions and customizations
- fully asynchronous design aiming for the best performance

### Installation
```bash
pip install binance-aio
```

### Prerequisites

Due to dependencies and Python features used by the library please make sure you use Python `3.6` or `3.7`.

Before starting using `binance-aio`, it is necessary to take care of:
1. downloading your Binance API and SECRET key from your binance account
1. generating your certificate that will be used to secure SSL connections. Certificate `certificate.pem` can be generated easily by
```bash
openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -keyout key.pem -out certificate.pem
```

### Examples
#### REST API
```python
import asyncio
import pathlib
import logging
import os
from datetime import datetime

from binance.BinanceClient import BinanceClient
from binance.Pair import Pair
from binance.enums import OrderSide, TimeInForce, OrderResponseType

LOG = logging.getLogger("binance")
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.StreamHandler())

print(f"Available loggers: {[name for name in logging.root.manager.loggerDict]}\n")

async def account_update(response : dict) -> None:
	print(f"Callback {account_update.__name__}: [{response}]")

async def order_book_update(response : dict) -> None:
	print(f"Callback {order_book_update.__name__}: [{response}]")

async def trade_update(response : dict) -> None:
	local_timestamp_ms = int(datetime.now().timestamp() * 1000)
	server_timestamp_ms = response['E']
	print(f"Trade update timestamp diff [ms]: {local_timestamp_ms - server_timestamp_ms}")

async def orderbook_ticker_update(response : dict) -> None:
	print(f"Callback {orderbook_ticker_update.__name__}: [{response}]")

async def run():
	print("STARTING BINANCE CLIENT\n")

	# to generate a certificate use 'openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -keyout key.pem -out certificate.pem'
	certificate_path = pathlib.Path(__file__).with_name("certificate.pem")

	# to retrieve your API/SEC key go to your binance website, create the keys and store them in APIKEY/SECKEY
	# environment variables
	api_key = os.environ['APIKEY']
	sec_key = os.environ['SECKEY']

	client = BinanceClient(certificate_path, api_key, sec_key)

	# REST api calls
	print("REST API")

	print("\nPing:")
	await client.ping()

	print("\nServer time:")
	await client.get_time()

	print("\nExchange info:")
	await client.get_exchange_info()

	print("\nBest order book ticker:")
	await client.get_best_orderbook_ticker(pair = Pair('ETH', 'BTC'))

	print("\nAccount:")
	await client.get_account(recv_window_ms = 5000)

	print("\nCreate limit order:")
	await client.create_limit_order(Pair("ETH", "BTC"), OrderSide.BUY, "1", "0", time_in_force = TimeInForce.GOOD_TILL_CANCELLED,
	                                new_order_response_type = OrderResponseType.FULL)

	print("\nDelete order:")
	await client.delete_order(pair = Pair('ETH', 'BTC'), order_id = "1")

	await client.close()

if __name__ == "__main__":
	asyncio.run(run())
```

#### WEBSOCKETS
```python
import asyncio
import pathlib
import logging
import os
from datetime import datetime

from binance.BinanceClient import BinanceClient
from binance.Pair import Pair
from binance.subscriptions import BestOrderBookTickerSubscription, TradeSubscription, AccountSubscription

LOG = logging.getLogger("binance")
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.StreamHandler())

print(f"Available loggers: {[name for name in logging.root.manager.loggerDict]}\n")

async def account_update(response : dict) -> None:
	print(f"Callback {account_update.__name__}: [{response}]")

async def order_book_update(response : dict) -> None:
	print(f"Callback {order_book_update.__name__}: [{response}]")

async def trade_update(response : dict) -> None:
	local_timestamp_ms = int(datetime.now().timestamp() * 1000)
	server_timestamp_ms = response['E']
	print(f"Trade update timestamp diff [ms]: {local_timestamp_ms - server_timestamp_ms}")

async def orderbook_ticker_update(response : dict) -> None:
	print(f"Callback {orderbook_ticker_update.__name__}: [{response}]")

async def run():
	print("STARTING BINANCE CLIENT\n")

	# to generate a certificate use 'openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -keyout key.pem -out certificate.pem'
	certificate_path = pathlib.Path(__file__).with_name("certificate.pem")

	# to retrieve your API/SEC key go to your binance website, create the keys and store them in API_KEY/SEC_KEY
	# environment variables
	api_key = os.environ['APIKEY']
	sec_key = os.environ['SECKEY']

	client = BinanceClient(certificate_path, api_key, sec_key)

	# Websockets
	print("\nWEBSOCKETS\n")

	print("\nCreate listen key:")
	listen_key = await client.get_listen_key()

	# Bundle several subscriptions into a single websocket
	client.compose_subscriptions([
		BestOrderBookTickerSubscription(callbacks = [orderbook_ticker_update]),
		TradeSubscription(pair = Pair('ETH', 'BTC'), callbacks = [trade_update])
	])

	# Bundle another subscriptions into a separate websocket
	print(listen_key)
	client.compose_subscriptions([
		AccountSubscription(client, callbacks = [account_update])
	])

	# Execute all websockets asynchronously
	await client.start_subscriptions()

	await client.close()

if __name__ == "__main__":
	asyncio.run(run())
```

All examples can be found in `client-example/client.py` in the GitHub repository.

### Support

If you like the library and you feel like you want to support its further development, enhancements and bugfixing, then it will be of great help and most appreciated if you:
- file bugs, proposals, pull requests, ...
- spread the word
- donate an arbitrary tip
  * BTC: 15JUgVq3YFoPedEj5wgQgvkZRx5HQoKJC4
  * ETH: 0xf29304b6af5831030ba99aceb290a3a2129b993d
  * ADA: DdzFFzCqrhshyLV3wktXFvConETEr9mCfrMo9V3dYz4pz6yNq9PjJusfnn4kzWKQR91pWecEbKoHodPaJzgBHdV2AKeDSfR4sckrEk79
  * XRP: rhVWrjB9EGDeK4zuJ1x2KXSjjSpsDQSaU6 **+ tag** 599790141

### Contact

If you feel you want to get in touch, then please

- preferably use Github Issues, or
- send an e-mail to <img src="http://safemail.justlikeed.net/e/160b5d5ea6878dd3d893b9f9fecb6ed7.png" border="0" align="absbottom">

### Affiliation

In case you are interested in an automated trading bot, check out our other project [creten](https://github.com/nardew/creten).
