#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import random
import logging
from kumex.client import Trade
import okex.swap_api as swap


def log_setting():
    logging.basicConfig(filename='log.log',
                        format='%(asctime)s - %(levelname)s - %(module)s - %(lineno)d:  %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S %p',
                        level=logging.INFO)


class Kumex(object):

    def __init__(self):
        # read configuration from json file
        with open('config.json', 'r') as file:
            config = json.load(file)

        self.ok_api_key = config['ok_api_key']
        self.ok_secret_key = config['ok_secret_key']
        self.ok_pass_phrase = config['ok_pass_phrase']
        self.kumex_api_key = config['kumex_api_key']
        self.kumex_secret_key = config['kumex_secret_key']
        self.kumex_pass_phrase = config['kumex_pass_phrase']
        self.is_sandbox = config['is_sandbox']
        self.interval = config['interval']
        self.maker_number = config['maker_number']
        self.taker_number = config['taker_number']
        # OK 永续合约API
        self.swapAPI = swap.SwapAPI(self.ok_api_key, self.ok_secret_key, self.ok_pass_phrase)
        self.trade = Trade(self.kumex_api_key, self.kumex_secret_key, self.kumex_pass_phrase,
                           is_sandbox=self.is_sandbox)

    def get_swap_market_price(self, symbol):
        r = self.swapAPI.get_mark_price(symbol)
        return int(float(r['mark_price']))


if __name__ == '__main__':
    log_setting()
    logging.info('---------------------------------------')
    logging.info('Service Start ......')
    service = Kumex()
    while 1:
        time.sleep(0.5)
        # 永续合约
        # 公共-获取合约信息 （20次/2s）
        # result = kumex.swapAPI.get_instruments()
        # 公共-获取合约标记价格 （20次/2s）
        market_price = service.get_swap_market_price('BTC-USDT-SWAP')
        logging.info('标记价格 = %s' % market_price)
        # taker
        tn = 1
        contract = 'XBTUSDTM'
        while tn <= service.taker_number:
            try:
                sell = service.trade.create_market_order(contract, 'sell', '1', type='market')
                logging.info('在合约 %s 吃卖单,订单ID = %s' %
                             (contract, sell['orderId']))
            except Exception as e:
                logging.error(e)
                break
            try:
                buy = service.trade.create_market_order(contract, 'buy', '1', type='market')
                logging.info('在合约 %s 吃买单,订单ID = %s' %
                             (contract, buy['orderId']))
            except Exception as e:
                logging.error(e)
                break
            tn += 1
        # maker
        mn = 1
        while mn <= service.maker_number:
            n = random.randint(1, 2000)
            try:
                ask = service.trade.create_limit_order(contract, 'sell', '1', n, market_price + mn)
                logging.info('在合约 %s 以数量= %s,价格= %s,创建了卖单,卖单ID = %s' %
                             (contract, n, market_price + mn, ask['orderId']))
            except Exception as e:
                logging.error(e)
                break
            m = random.randint(1, 2000)
            try:
                bid = service.trade.create_limit_order(contract, 'buy', '1', m, market_price - mn)
                logging.info('在合约 %s 以数量= %s,价格= %s,创建了买单,卖单ID = %s' %
                             (contract, m, market_price - mn, bid['orderId']))
            except Exception as e:
                logging.error(e)
                break
            mn += 1
        logging.info('mn = %s' % mn)

        logging.info('---------------------------------------')
        break
