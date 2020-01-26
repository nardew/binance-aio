import enum

class RestCallType(enum.Enum):
	GET = enum.auto()
	POST = enum.auto()
	DELETE = enum.auto()

class OrderSide(enum.Enum):
	BUY = "BUY"
	SELL = "SELL"

class OrderResponseType(enum.Enum):
	ACT = "ACK"
	RESULT = "RESULT"
	FULL = "FULL"

class TimeInForce(enum.Enum):
	GOOD_TILL_CANCELLED = "GTC"
	IMMEDIATE_OR_CANCELLED = "IOC"
	FILL_OR_KILL = "FOK"

class TimeUnit(enum.Enum):
	MINUTES = "MINUTES"
	HOURS = "HOURS"
	DAYS = "DAYS"
	WEEKS = "WEEKS"
	MONTHS = "MONTHS"
