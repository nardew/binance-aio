import websockets
import json
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import List, Callable, Any

from binance.Pair import Pair

LOG = logging.getLogger(__name__)

class Subscription(ABC):
	def __init__(self, callbacks = None):
		self.callbacks = callbacks

	@abstractmethod
	def get_channel_name(self) -> str:
		pass

	async def initialize(self) -> None:
		pass

	async def process_message(self, response : dict) -> None:
		await self.process_callbacks(response)

	async def process_callbacks(self, response : dict) -> None:
		if self.callbacks is not None:
			await asyncio.gather(*[asyncio.create_task(cb(response)) for cb in self.callbacks])


class SubscriptionMgr(object):
	WEB_SOCKET_URI = "wss://stream.binance.com:9443/"

	SUBSCRIPTION_ID = 0

	def __init__(self, subscriptions : List[Subscription], api_key : str, ssl_context = None):
		self.api_key = api_key
		self.ssl_context = ssl_context

		self.subscriptions = subscriptions

	async def run(self) -> None:
		for subscription in self.subscriptions:
			await subscription.initialize()

		try:
			# main loop ensuring proper reconnection after a graceful connection termination by the remote server
			while True:
				LOG.debug(f"Initiating websocket connection.")
				uri = SubscriptionMgr.WEB_SOCKET_URI + self._create_stream_uri()
				LOG.debug(f"Websocket uri: {uri}")
				async with websockets.connect(uri, ssl = self.ssl_context) as websocket:
					subscription_message = self._create_subscription_message()
					LOG.debug(f"> {subscription_message}")
					await websocket.send(json.dumps(subscription_message))

					# start processing incoming messages
					while True:
						response = json.loads(await websocket.recv())
						LOG.debug(f"< {response}")

						if self._is_subscription_confirmation(response):
							LOG.info(f"Subscription confirmed for id: {response['id']}")
						# regular message
						else:
							await self.process_message(response)
		except asyncio.CancelledError:
			LOG.warning(f"Websocket requested to be shutdown.")
		except Exception:
			LOG.error(f"Exception occurred. Websocket will be closed.")
			raise

	def _create_subscription_message(self) -> dict:
		SubscriptionMgr.SUBSCRIPTION_ID += 1

		return {
			"method": "SUBSCRIBE",
			"params": [
				subscription.get_channel_name() for subscription in self.subscriptions
			],
			"id": SubscriptionMgr.SUBSCRIPTION_ID
		}

	def _create_stream_uri(self) -> str:
		return "stream?streams=" + "/".join([subscription.get_channel_name() for subscription in self.subscriptions])

	@staticmethod
	def _is_subscription_confirmation(response):
		if 'result' in response and response['result'] is None:
			return True
		else:
			return False

	async def process_message(self, response : dict) -> None:
		for subscription in self.subscriptions:
			if subscription.get_channel_name() == response["stream"]:
				await subscription.process_message(response["data"])
				break

class BestOrderBookTickerSubscription(Subscription):
	def __init__(self, callbacks : List[Callable[[dict], Any]] = None):
		super().__init__(callbacks)

	def get_channel_name(self):
		return "!bookTicker"

class TradeSubscription(Subscription):
	def __init__(self, pair : Pair, callbacks: List[Callable[[dict], Any]] = None):
		super().__init__(callbacks)

		self.pair = pair

	def get_channel_name(self):
		return str(self.pair).lower() + "@trade"

class AccountSubscription(Subscription):
	def __init__(self, binance_client, callbacks: List[Callable[[dict], Any]] = None):
		super().__init__(callbacks)

		self.binance_client = binance_client
		self.listen_key = None

	async def initialize(self):
		listen_key_response = await self.binance_client.get_listen_key()
		self.listen_key = listen_key_response["response"]["listenKey"]
		LOG.debug(f'Listen key: {self.listen_key}')

	def get_channel_name(self):
		return self.listen_key