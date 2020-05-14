#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import threading
from multiprocessing import Process
import time
import random
import logging
import consts as c
from kumex.client import Trade
import okex.swap_api as swap
import okex.futures_api as future


def log_setting():
    logging.basicConfig(filename=c.LOG_FILE,
                        format='%(asctime)s - %(levelname)s - %(module)s - %(lineno)d:  %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S %p',
                        level=logging.INFO)


class Kumex(object):

    def __init__(self):
        # read configuration from json file
        with open(c.CONFIG_FILE, 'r') as file:
            config = json.load(file)

        self.ok_api_key = config['ok_api_key']
        self.ok_secret_key = config['ok_secret_key']
        self.ok_pass_phrase = config['ok_pass_phrase']
        self.kumex_api_key = config['kumex_api_key']
        self.kumex_secret_key = config['kumex_secret_key']
        self.kumex_pass_phrase = config['kumex_pass_phrase']
        self.is_sandbox = config['is_sandbox']
        self.ok_symbol = config['ok_symbol']
        self.kumex_symbol = config['kumex_symbol']
        self.category = config['category']
        self.interval = config['interval']
        self.maker_number = config['maker_number']
        self.taker_number = config['taker_number']
        self.side = config['side']
        # OK 永续合约API
        self.swapAPI = swap.SwapAPI(self.ok_api_key, self.ok_secret_key, self.ok_pass_phrase)
        # OK 交割合约
        self.futureAPI = future.FutureAPI(self.ok_api_key, self.ok_secret_key, self.ok_pass_phrase)

        self.trade = Trade(self.kumex_api_key, self.kumex_secret_key, self.kumex_pass_phrase,
                           is_sandbox=self.is_sandbox)

    def get_market_price(self):
        r = {}
        # 根据类型调用对应的合约API
        if self.category == c.SWAP:
            r = self.swapAPI.get_mark_price(self.ok_symbol)
        elif self.category == c.FUTURE:
            r = self.futureAPI.get_mark_price(self.ok_symbol)

        market_price = int(float(r['mark_price']))

        # randint = random.randint(-20, 20)
        # market_price += randint
        logging.info('标记价格 = %s' % market_price)
        return market_price

    def taker(self):
        try:
            t = random.randint(1, 5000)
            sell = self.trade.create_market_order(self.kumex_symbol, 'sell', '1', type='market', size=t)
            logging.info('在合约 %s 以数量= %s 吃卖单,订单ID = %s' %
                         (self.kumex_symbol, t, sell['orderId']))
        except Exception as e:
            logging.error(e)
        try:
            t = random.randint(1, 5000)
            buy = self.trade.create_market_order(self.kumex_symbol, 'buy', '1', type='market', size=t)
            logging.info('在合约 %s 以数量= %s 吃买单,订单ID = %s' %
                         (self.kumex_symbol, t, buy['orderId']))
        except Exception as e:
            logging.error(e)

    def ask_maker(self):
        mn = 1
        price = self.get_market_price()
        while mn < self.maker_number:
            try:
                m = random.randint(1, 5000)
                ap = price + mn
                ask = self.trade.create_limit_order(self.kumex_symbol, 'sell', '1', m, ap)
                logging.info('在合约 %s 以数量= %s,价格= %s,创建了卖单,卖单ID = %s' %
                             (self.kumex_symbol, m, ap, ask['orderId']))
            except Exception as e:
                logging.error(e)

            mn += 1

    def bid_maker(self):
        mn = 1
        price = self.get_market_price()
        while mn < self.maker_number:
            try:
                m = random.randint(1, 5000)
                bp = price - mn
                bid = self.trade.create_limit_order(self.kumex_symbol, 'buy', '1', m, bp)
                logging.info('在合约 %s 以数量= %s,价格= %s,创建了买单,卖单ID = %s' %
                             (self.kumex_symbol, m, bp, bid['orderId']))
            except Exception as e:
                logging.error(e)

            mn += 1


if __name__ == '__main__':
    log_setting()
    logging.info('---------------------------------------')
    logging.info('Service Start ......')
    service = Kumex()
    while 1:
        if service.side == 'taker':
            service.taker()
            time.sleep(1)
        elif service.side == 'ask_maker':
            service.ask_maker()
        elif service.side == 'bid_maker':
            service.bid_maker()

