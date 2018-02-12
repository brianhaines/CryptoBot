#!/usr/bin/env python3
import pandas as pd
import time
import numpy as np
import sys
import datetime as datetime
import matplotlib.pyplot as plt
from settings import DBNAME
from settings import DB_USER
from settings import DB_PASSWORD
import pymysql
from sqlalchemy import create_engine


def backtester():
	df = pd.DataFrame()
	engine_txt = 'mysql+pymysql://{0}:{1}@localhost/{2}'.format(DB_USER,DB_PASSWORD,DBNAME)
	engine = create_engine(engine_txt)

	sql = '''SELECT * FROM ticks WHERE product = 'ETH-USD' AND time between "2018-02-11T22:23:10.804000Z" and "2018-02-12T03:54:33.088000Z"'''
	
	df = pd.read_sql_query(sql,engine)

	df = df.astype({'price':'float64','bid':'float64','ask':'float64','spread':'float64','size':'float64'})

	df.index = pd.DatetimeIndex(df['time'])

	cols = []
	strats = []

	for short_mom in [30, 40, 50]:
		col = 'short_{0}'.format(short_mom)
		df[col] = df['bid'].rolling(short_mom).mean()
		cols.append(col)
		for long_mom_fact in [5, 6, 7]:
			long_mom = short_mom*long_mom_fact
			col = 'long_{0}'.format(long_mom)
			df[col] = df['bid'].rolling(long_mom).mean()
			cols.append(col)
			strat = 'strat_{0}_{1}'.format(short_mom,long_mom)
			strats.append(strat)

			
	#print(df.head())
	for col in strats:
		print(col)


if __name__ == '__main__':
    backtester()