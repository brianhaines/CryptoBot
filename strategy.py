#!/usr/bin/env python3
from event import SignalEvent
from settings import SMA_Periods #short and long
import copy
from decimal import Decimal, getcontext, ROUND_HALF_DOWN

class MovingAverageStrategy(object):
	def __init__(self, products, events):
		self.products = products
		self.events = events
		#self.df = pd.DataFrame()
		self.momentum = SMA_Periods
		self.signal = None
		self.pairs_dict = self.create_pairs_dict()

	def create_pairs_dict(self):
		attr_dict = {
			"ticks": 0,
			"invested": False,
			"short_sma": None,
			"long_sma": None
		}
		pairs_dict = {}
		for p in self.products:
			pairs_dict[p] = copy.deepcopy(attr_dict)
		return pairs_dict

	def calc_rolling_sma(self, sma_m_1, window, price):
		return Decimal(((sma_m_1 * (window - 1)) + price) / window).quantize(Decimal('0.01'),rounding=ROUND_HALF_DOWN)

	def calculateSignal(self, event):
		if event.type == 'TICK':
			pd = self.pairs_dict[event.product]
			if pd["ticks"] == 0:
				pd["short_sma"] = event.bid
				pd["long_sma"] = event.bid
			else:
				pd["short_sma"] = self.calc_rolling_sma(
					pd["short_sma"], self.momentum['short'], event.bid
				)
				pd["long_sma"] = self.calc_rolling_sma(
					pd["long_sma"], self.momentum['long'], event.bid
				)

			# Only start the strategy when we have created an accurate short window
			if pd["ticks"] > self.momentum['short']:
				if pd["short_sma"] > pd["long_sma"]:
					signal = SignalEvent(event.product, "limit", "buy", event.time,pd)
					self.events.put(signal)
					print('{0} Short / Long: {1} / {2}'.format(event.product, pd["short_sma"],pd["long_sma"]))

				if pd["short_sma"] < pd["long_sma"]:
					signal = SignalEvent(event.product, "limit", "sell", event.time,pd)
					self.events.put(signal)
					#print('{0} Short / Long: {1} / {2}'.format(event.product, pd["short_sma"],pd["long_sma"]))
			else:
				print('{0} ticks {1} and short {2} and long {3}'.format(event.product,pd["ticks"],self.momentum['short'],self.momentum['long']))
			
			pd["ticks"] += 1
			self.pairs_dict[event.product] = copy.deepcopy(pd)


