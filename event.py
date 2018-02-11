#!/usr/bin/env python3


class Event(object):
    pass


class TickEvent(Event):
    def __init__(self, product, time, sequence, price, bid, ask, spread, side, size):
        self.type = 'TICK'
        self.sequence = sequence
        self.product = product
        self.time = time
        self.price = price
        self.bid = bid
        self.ask = ask
        self.spread = round(float(ask) - float(bid),2)
        self.side = side
        self.size = size