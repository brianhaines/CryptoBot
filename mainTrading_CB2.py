#!/usr/bin/env python3
from settings import API_KEY
from settings import API_SECRET
from settings import API_PASSPHRASE
from settings import PRODUCTS
from event import TickEvent
from decimal import Decimal, getcontext, ROUND_HALF_DOWN
import logging
import queue
import threading
import time
import gdax



class CryptoBot(gdax.WebsocketClient):
	def __init__(self, product=None, events=None, key=None, secret=None, passphrase=None, channel=None):
		super(CryptoBot, self).__init__(products=product, channels=channel)


	def on_open(self):
		self.events_queue = events
		self.url = "wss://ws-feed.gdax.com/"
		self.message_count = 0
		print("Let the streaming begin!")

	def on_message(self,msg):
		b = len(PRODUCTS)
		if msg['type'] == 'ticker':
			if self.message_count > b:
				self.events_queue.put(
					TickEvent(
						product		=	msg['product_id'],
						sequence	=	msg['sequence'],
			 			time		=	msg['time'], 
						price		=	Decimal(msg['price']),
						bid			=	Decimal(msg['best_bid']),
						ask			=	Decimal(msg['best_ask']),
						spread		=	Decimal(msg['best_ask']) - Decimal(msg['best_bid']),
						side		=	msg['side'],
						size		=	Decimal(msg['last_size']).quantize(Decimal('0.000000001'),rounding=ROUND_HALF_DOWN)
						)
					)
		else:
			print(msg)

		self.message_count += 1

	def on_close(self):
		print('Closing time!')

def trade(events):
	latestPrices= {}
	latestPrices['USD-USD'] = {"bid": Decimal("1.0"), "ask": Decimal("1.0"),"last":Decimal("1.0")}


	try:
		while True:
			try:
				event = events.get(False)
			except queue.Empty:
				pass
			else:
				if event is not None:
					if event.type == 'TICK':
						# Define the current market
						latestPrices[event.product] = {'bid':event.bid,'ask':event.ask,'last':event.price}

						if event.product == 'ETH-BTC':
							# Buy BTC-USD, buy ETH-BTC, sell ETH-USD
							legz = latestPrices['ETH-USD']['ask'] / latestPrices['BTC-USD']['ask'] - latestPrices['ETH-BTC']['bid']
							print('The {0} arbitrage is {1}'.format(event.product, legz))
						elif event.sequence % 25 == 0 or event.size > 1:
							print('This is a {0} Tick: {1} and {2} / {3}'.format(
										event.product,
										latestPrices[event.product]['last'],
										latestPrices[event.product]['bid'],
										latestPrices[event.product]['ask']
										))

	except KeyboardInterrupt:
		print('Closing Time')
		CryptoBot.close()
		conn.close()

if __name__ == '__main__':
	channel = ['ticker']
	events = queue.Queue()

	# Streaming prices
	streamingPrices = CryptoBot(
							product 	=	PRODUCTS, 
							channel 	=	channel, 																																																																																											
							events 		=	events,
							secret		= 	API_SECRET,
							key 		=	API_KEY,
							passphrase	=	API_PASSPHRASE
							)

	trade_thread = threading.Thread(target=trade, args=(events,))

	streamingPrices.start()
	trade_thread.start()
	