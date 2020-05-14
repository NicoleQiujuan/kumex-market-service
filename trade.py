#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
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
        # OK 永续合约API
        self.swapAPI = swap.SwapAPI(self.ok_api_key, self.ok_secret_key, self.ok_pass_phrase)
        # OK 交割合约
        self.futureAPI = future.FutureAPI(self.ok_api_key, self.ok_secret_key, self.ok_pass_phrase)

        self.trade = Trade(self.kumex_api_key, self.kumex_secret_key, self.kumex_pass_phrase,
                           is_sandbox=self.is_sandbox)

    def get_market_price(self, category, symbol):
        r = {}
        # 根据类型调用对应的合约API
        if category == c.SWAP:
            r = self.swapAPI.get_mark_price(symbol)
        elif category == c.FUTURE:
            r = self.futureAPI.get_mark_price(symbol)

        return int(float(r['mark_price']))


if __name__ == '__main__':
    log_setting()
    logging.info('---------------------------------------')
    logging.info('Service Start ......')
    service = Kumex()
    while 1:
        time.sleep(1)
        # 公共-获取合约标记价格 （20次/2s）
        market_price = service.get_market_price(service.category, service.ok_symbol)
        logging.info('标记价格 = %s' % market_price)
        if market_price > 0:
            # taker
            try:
                t = random.randint(1, 5000)
                sell = service.trade.create_market_order(service.kumex_symbol, 'sell', '1', type='market', size=t)
                logging.info('在合约 %s 以数量= %s 吃卖单,订单ID = %s' %
                             (service.kumex_symbol, t, sell['orderId']))
            except Exception as e:
                logging.error(e)
            try:
                t = random.randint(1, 5000)
                buy = service.trade.create_market_order(service.kumex_symbol, 'buy', '1', type='market', size=t)
                logging.info('在合约 %s 以数量= %s 吃买单,订单ID = %s' %
                             (service.kumex_symbol, t, buy['orderId']))
            except Exception as e:
                logging.error(e)
            # maker
            mn = 1
            while mn <= service.maker_number:
                try:
                    m = random.randint(1, 5000)
                    rn = random.randint(-20, 20)
                    ap = market_price + mn + rn
                    ask = service.trade.create_limit_order(service.kumex_symbol, 'sell', '1', m, ap)
                    logging.info('在合约 %s 以数量= %s,价格= %s,创建了卖单,卖单ID = %s' %
                                 (service.kumex_symbol, m, ap, ask['orderId']))
                except Exception as e:
                    logging.error(e)
                    continue
                try:
                    m = random.randint(1, 5000)
                    rn = random.randint(-20, 20)
                    bp = market_price - mn + rn
                    bid = service.trade.create_limit_order(service.kumex_symbol, 'buy', '1', m, bp)
                    logging.info('在合约 %s 以数量= %s,价格= %s,创建了买单,卖单ID = %s' %
                                 (service.kumex_symbol, m, bp, bid['orderId']))
                except Exception as e:
                    logging.error(e)
                    continue
                mn += 1

