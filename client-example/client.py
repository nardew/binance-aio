import asyncio
import pathlib
import logging
import os
from datetime import datetime

from binance.BinanceClient import BinanceClient
from binance.Pair import Pair
from binance.subscriptions import BestOrderBookTickerSubscription, TradeSubscription, AccountSubscription
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

	# to retrieve your API/SEC key go to your binance website, create the keys and store them in API_KEY/SEC_KEY
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
