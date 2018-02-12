#!/usr/bin/env python3
from settings import API_KEY
from settings import API_SECRET
from settings import API_PASSPHRASE
from settings import PRODUCTS
from settings import DBNAME
from settings import DB_USER
from settings import DB_PASSWORD
from event import TickEvent
from strategy import MovingAverageStrategy
from decimal import Decimal, getcontext, ROUND_HALF_DOWN
import pymysql.cursors
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

def trade(events,strategy):
	latestPrices= {}
	latestPrices['USD-USD'] = {"bid": Decimal("1.0"), "ask": Decimal("1.0"),"last":Decimal("1.0")}
	arbitrages = {}
	arbitrages['ETH-BTC'] = {'in':Decimal('0.0000'),'out':Decimal('0.0000'),'spread':Decimal('0.0000')}

	for prod in PRODUCTS:
		latestPrices[prod] = {"bid": None, "ask": None,"last":None}

	conn = pymysql.connect(host='localhost',
						user=DB_USER,
						password=DB_PASSWORD, 
						db=DBNAME,
						cursorclass=pymysql.cursors.DictCursor)

	try:
		while True:
			try:
				event = events.get(False)
			except queue.Empty:
				pass
			else:
				if event is not None:
					if event.type == 'TICK':
						latestPrices[event.product] = {'bid':event.bid,'ask':event.ask,'last':event.price}

						# Send tick to strategy
						strategy.calculateSignal(event)

						with conn.cursor() as cursor:
							sql = '''INSERT INTO ticks(sequence, product, time, price, bid, ask, spread, side, size) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)'''	
							cursor.execute(sql,(event.sequence, event.product, event.time, event.price, event.bid, event.ask, event.spread, event.side, event.size))
						conn.commit()

						if event.product == 'ETH-BTC':
							# Buy BTC-USD, buy ETH-BTC, sell ETH-USD
							arbitrages[event.product]['in'] = latestPrices['ETH-USD']['bid'] / latestPrices['BTC-USD']['ask'] - latestPrices['ETH-BTC']['ask']
							# Buy ETH-USD, sell ETH-BTC, sell BTC-USD
							arbitrages[event.product]['out'] = latestPrices['ETH-USD']['ask'] / latestPrices['BTC-USD']['bid'] - latestPrices['ETH-BTC']['bid']
							# Arb spread
							arbitrages[event.product]['spread'] = arbitrages[event.product]['out'] - arbitrages[event.product]['in']

							with conn.cursor() as cursor:
								sql = '''INSERT INTO arbitrage(product, time, arb_in, arb_out, arb_spread, arb_size_in, arb_size_out) VALUES(%s,%s,%s,%s,%s,%s,%s)'''	
								cursor.execute(sql,(event.product, event.time, round(arbitrages[event.product]['in'],9), 
									round(arbitrages[event.product]['out'],9), round(arbitrages[event.product]['spread'],9),None,None))
							conn.commit()
							
						elif event.sequence % 25 == 0 or event.size > 2:
							print('This is a {0} Tick: {1} and {2} / {3}'.format(
								event.product,
								latestPrices[event.product]['last'],
								latestPrices[event.product]['bid'],
								latestPrices[event.product]['ask']
								))
					elif event.type == 'SIGNAL':
						print('This is a SIGNAL: {0} {1} params: {2}/{3}'.format(event.side,event.market,event.sig_params['short_sma'],event.sig_params['long_sma']))

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
	
	# The trading strategy
	strategy = MovingAverageStrategy(PRODUCTS, events)

	trade_thread = threading.Thread(target=trade, args=(events, strategy))

	streamingPrices.start()
	trade_thread.start()
	