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
        self.maker_number = config['maker_number']
        self.taker_number = config['taker_number']
        self.side = config['side']
        self.sizeMin = 100
        self.sizeMax = 100000
        # OK 永续合约API
        self.swapAPI = swap.SwapAPI(self.ok_api_key, self.ok_secret_key, self.ok_pass_phrase)
        # OK 交割合约
        self.futureAPI = future.FutureAPI(self.ok_api_key, self.ok_secret_key, self.ok_pass_phrase)

        self.buy_list = {}
        self.sell_list = {}
        self.best_ask = 0
        self.best_bid = 0
        self.market_price = 0
        self.mutex = threading.Lock()

        self.trade = Trade(self.kumex_api_key, self.kumex_secret_key, self.kumex_pass_phrase,
                           is_sandbox=self.is_sandbox)

    def get_market_price(self):
        r = {}
        # 根据类型调用对应的合约API
        try:
            if self.category == c.SWAP:
                r = self.swapAPI.get_specific_ticker(self.ok_symbol)
            elif self.category == c.FUTURE:
                r = self.futureAPI.get_specific_ticker(self.ok_symbol)
        except Exception as e:
            logging.error(e)
            time.sleep(1)
        self.best_ask = int(float(r['best_ask']))
        # logging.info('最新卖一价格 = %s' % self.best_ask)
        self.best_bid = int(float(r['best_bid']))
        # logging.info('最新买一价格 = %s' % self.best_bid)
        self.market_price = int((self.best_ask+self.best_bid) / 2)
        logging.info('最新盘口价格 = %s' % self.market_price)

    def taker(self):
        try:
            t = random.randint(self.sizeMin, self.sizeMax)
            sell = self.trade.create_market_order(self.kumex_symbol, 'sell', '1', type='market', size=t)
            logging.info('在合约 %s 以数量= %s 吃卖单,订单ID = %s' %
                         (self.kumex_symbol, t, sell['orderId']))
        except Exception as e:
            logging.error(e)
        try:
            t = random.randint(self.sizeMin, self.sizeMax)
            buy = self.trade.create_market_order(self.kumex_symbol, 'buy', '1', type='market', size=t)
            logging.info('在合约 %s 以数量= %s 吃买单,订单ID = %s' %
                         (self.kumex_symbol, t, buy['orderId']))
        except Exception as e:
            logging.error(e)

    def ask_maker(self, p):
        try:
            m = random.randint(self.sizeMin, self.sizeMax)
            ask = self.trade.create_limit_order(self.kumex_symbol, 'sell', '5', m, p)
            logging.info('当前盘口价格 = %s,在合约 %s 以数量= %s,价格= %s,创建了卖单,卖单ID = %s' %
                         (self.market_price, self.kumex_symbol, m, p, ask['orderId']))
            self.sell_list[p] = {
                'price': p,
                'side': 'sell',
                'size': m,
                'order_id': ask['orderId']
            }
        except Exception as e:
            logging.error(e)

    def bid_maker(self, p):
        try:
            m = random.randint(self.sizeMin, self.sizeMax)
            bid = self.trade.create_limit_order(self.kumex_symbol, 'buy', '5', m, p)
            logging.info('当前盘口价格 = %s,在合约 %s 以数量= %s,价格= %s,创建了买单,卖单ID = %s' %
                         (self.market_price, self.kumex_symbol, m, p, bid['orderId']))
            self.sell_list[p] = {
                'price': p,
                'side': 'buy',
                'size': m,
                'order_id': bid['orderId']
            }
        except Exception as e:
            logging.error(e)

    def cancel_order(self, order_id, key):
        try:
            self.trade.cancel_order(order_id)
            logging.info('撤单 id = %s, key = %s' % (order_id, key))
        except Exception as e:
            logging.info('order_id = %s, key = %s' % (order_id, key))
            logging.error(e)

    def get_order_info(self, order_id):
        try:
            o = self.trade.get_order_details(order_id)
        except Exception as e:
            logging.error(e)
            o = {}
        return o

    def get_active_orders(self):
        try:
            o = self.trade.get_order_list(symbol=self.kumex_symbol, status='active')
            os = o['items']
        except Exception as e:
            logging.error(e)
            os = []
        if len(os) > 0:
            self.sell_list.clear()
            self.buy_list.clear()
            for n in os:
                if n['side'] == 'sell':
                    self.sell_list[int(n['price'])] = {
                        'price': int(n['price']),
                        'side': 'sell',
                        'size': n['size'],
                        'order_id': n['id']
                    }
                elif n['side'] == 'buy':
                    self.buy_list[int(n['price'])] = {
                        'price': int(n['price']),
                        'side': 'buy',
                        'size': n['size'],
                        'order_id': n['id']
                    }


if __name__ == '__main__':
    log_setting()
    logging.info('---------------------------------------')
    logging.info('Service Start ......')
    service = Kumex()
    # cnt = 0
    while 1:
        # cnt += 1
        # print(cnt)
        if service.side == 'taker':
            service.taker()
            time.sleep(1)
        else:
            service.get_market_price()
            service.get_active_orders()
            logging.info('len(service.sell_list) = %s' % len(service.sell_list))
            logging.info(service.sell_list)
            # 价格浮动
            rand = random.randint(-20, 20)
            # service.market_price += rand
            ask_rand = service.market_price + 20
            service.mutex.acquire()
            for k, v in list(service.sell_list.items()):
                # 判断范围，不在范围内的单撤掉
                if k not in range(service.market_price, ask_rand) and k in service.sell_list.keys():
                    # logging.info('k not in range(service.market_price = %s' % k)
                    del service.sell_list[k]
                    cancel_order = threading.Thread(target=service.cancel_order, args=(v['order_id'], k,))
                    cancel_order.start()
                    # service.cancel_order(v['order_id'], k)
            service.mutex.release()
            # logging.info('after cancel ---')
            # logging.info(service.sell_list)

            for i in range(1, service.maker_number):
                ask_price = service.market_price + i
                # logging.info('for loop ask_price = %s' % ask_price)
                if ask_price in service.sell_list.keys():
                    # logging.info('ask_price in keys loop = %s' % ask_price)
                    orderId = service.sell_list[ask_price]['order_id']
                    order_info = service.get_order_info(orderId)
                    if order_info:
                        if not order_info['isActive']:
                            # logging.info('not order_info[isActive] = %s' % ask_price)
                            service.mutex.acquire()
                            ask_order = threading.Thread(target=service.ask_maker, args=(ask_price,))
                            ask_order.start()
                            service.mutex.release()
                            # service.ask_maker(ask_price)
                        else:
                            size_dff = order_info['size'] - order_info['dealSize']
                            if size_dff not in range(service.sizeMin, service.sizeMax):
                                if order_info['isActive']:
                                    # logging.info('del service.sell_list[ask_price] = %s' % ask_price)
                                    del service.sell_list[ask_price]
                                    service.mutex.acquire()
                                    cancel_order = threading.Thread(target=service.cancel_order,
                                                                    args=(order_info['id'], ask_price,))
                                    cancel_order.start()
                                    service.mutex.release()
                                    # service.cancel_order(order_info['id'], ask_price)
                                service.mutex.acquire()
                                ask_order = threading.Thread(target=service.ask_maker, args=(ask_price,))
                                ask_order.start()
                                service.mutex.release()
                                # service.ask_maker(ask_price)

                else:
                    # logging.info('target=service.ask_maker, = %s' % ask_price)
                    service.mutex.acquire()
                    ask_order = threading.Thread(target=service.ask_maker, args=(ask_price,))
                    ask_order.start()
                    service.mutex.release()
                    # service.ask_maker(ask_price)
            # logging.info('end cancel ---')
            # logging.info(service.sell_list)

            bid_rand = service.market_price - 20
            service.mutex.acquire()
            for k, v in list(service.buy_list.items()):
                # 判断范围，不在范围内的单撤掉
                if k not in range(bid_rand, service.market_price):
                    del service.buy_list[k]
                    cancel_order = threading.Thread(target=service.cancel_order, args=(v['order_id'], k,))
                    cancel_order.start()
            service.mutex.release()
            for i in range(1, service.maker_number):
                bid_price = service.market_price - i
                if bid_price in service.buy_list.keys():
                    orderId = service.buy_list[bid_price]['order_id']
                    order_info = service.get_order_info(orderId)
                    if order_info:
                        if not order_info['isActive']:
                            service.mutex.acquire()
                            bid_order = threading.Thread(target=service.ask_maker, args=(bid_price,))
                            bid_order.start()
                            service.mutex.release()
                        else:
                            size_dff = order_info['size'] - order_info['dealSize']
                            if size_dff not in range(service.sizeMin, service.sizeMax):
                                if order_info['isActive']:
                                    del service.buy_list[bid_price]
                                    service.mutex.acquire()
                                    cancel_order = threading.Thread(target=service.cancel_order,
                                                                    args=(order_info['id'], bid_price,))
                                    cancel_order.start()
                                    service.mutex.release()

                                service.mutex.acquire()
                                bid_order = threading.Thread(target=service.bid_maker, args=(bid_price,))
                                bid_order.start()
                                service.mutex.release()
                else:
                    service.mutex.acquire()
                    bid_order = threading.Thread(target=service.bid_maker, args=(bid_price,))
                    bid_order.start()
                    service.mutex.release()
