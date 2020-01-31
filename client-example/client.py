import asyncio
import pathlib
import logging
import os
from datetime import datetime

from binance.BinanceClient import BinanceClient
from binance.Pair import Pair
from binance.subscriptions import BestOrderBookTickerSubscription, TradeSubscription, AccountSubscription
from binance import enums
from binance.BinanceException import BinanceException

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

	print("\nOrder book:")
	await client.get_orderbook(pair = Pair('ETH', 'BTC'), limit = enums.DepthLimit.L_5)

	print("\nTrades:")
	await client.get_trades(pair=Pair('ETH', 'BTC'), limit = 5)

	print("\nHistorical trades:")
	await client.get_historical_trades(pair=Pair('ETH', 'BTC'), limit = 5)

	print("\nAggregate trades:")
	await client.get_aggregate_trades(pair=Pair('ETH', 'BTC'), limit = 5)

	print("\nCandelsticks:")
	await client.get_candelsticks(pair=Pair('ETH', 'BTC'), interval = enums.CandelstickInterval.I_1D, limit=5)

	print("\nAverage price:")
	await client.get_average_price(pair = Pair('ETH', 'BTC'))

	print("\n24hour price ticker:")
	await client.get_24h_price_ticker(pair = Pair('ETH', 'BTC'))

	print("\nProce ticker:")
	await client.get_price_ticker(pair = Pair('ETH', 'BTC'))

	print("\nBest order book ticker:")
	await client.get_best_orderbook_ticker(pair = Pair('ETH', 'BTC'))

	print("\nCreate test market order:")
	await client.create_test_order(Pair("ETH", "BTC"), side = enums.OrderSide.BUY, type = enums.OrderType.MARKET,
	                          quantity = "1",
	                          new_order_response_type = enums.OrderResponseType.FULL)

	print("\nCreate limit order:")
	try:
		await client.create_order(Pair("ETH", "BTC"), side = enums.OrderSide.BUY, type = enums.OrderType.LIMIT,
		                          quantity = "1",
		                          price = "0",
		                          time_in_force = enums.TimeInForce.GOOD_TILL_CANCELLED,
		                          new_order_response_type = enums.OrderResponseType.FULL)
	except BinanceException as e:
		print(e)

	print("\nCancel order:")
	try:
		await client.cancel_order(pair = Pair('ETH', 'BTC'), order_id = "1")
	except BinanceException as e:
		print(e)

	print("\nGet order:")
	try:
		await client.get_order(pair = Pair('ETH', 'BTC'), order_id = 1)
	except BinanceException as e:
		print(e)

	print("\nGet open orders:")
	await client.get_open_orders(pair = Pair('ETH', 'BTC'))

	print("\nGet all orders:")
	await client.get_all_orders(pair = Pair('ETH', 'BTC'))

	print("\nCreate OCO order:")
	try:
		await client.create_oco_order(Pair("ETH", "BTC"), side = enums.OrderSide.BUY,
		                          quantity = "1",
		                          price = "0",
		                          stop_price = "0",
		                          new_order_response_type = enums.OrderResponseType.FULL)
	except BinanceException as e:
		print(e)

	print("\nCancel OCO order:")
	try:
		await client.cancel_oco_order(pair = Pair('ETH', 'BTC'), order_list_id = "1")
	except BinanceException as e:
		print(e)

	print("\nGet OCO order:")
	try:
		await client.get_oco_order(order_list_id = 1)
	except BinanceException as e:
		print(e)

	print("\nGet open OCO orders:")
	await client.get_open_oco_orders()

	print("\nGet all OCO orders:")
	await client.get_all_oco_orders()

	print("\nAccount:")
	await client.get_account(recv_window_ms = 5000)

	print("\nAccount trades:")
	await client.get_account_trades(pair = Pair('ETH', 'BTC'))

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
	#await client.start_subscriptions()

	await client.close()

if __name__ == "__main__":
	asyncio.run(run())
