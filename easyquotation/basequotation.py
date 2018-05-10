# coding:utf8
import json
import warnings
from multiprocessing.pool import ThreadPool

import easyutils
import requests

from . import helpers


class BaseQuotation:
    """行情获取基类"""
    max_num = 800  # 每次请求的最大股票数
    stock_api = ''  # 股票 api

    def __init__(self):
        self._session = requests.session()
        stock_codes = self.load_stock_codes()
        self.stock_list = self.gen_stock_list(stock_codes)

    def gen_stock_list(self, stock_codes):
        stock_with_exchange_list = [easyutils.stock.get_stock_type(code) + code[-6:] for code in stock_codes]

        if len(stock_with_exchange_list) < self.max_num:
            request_list = ','.join(stock_with_exchange_list)
            return [request_list]

        stock_list = []
        request_num = len(stock_codes) // self.max_num + 1
        for range_start in range(request_num):
            num_start = self.max_num * range_start
            num_end = self.max_num * (range_start + 1)
            request_list = ','.join(stock_with_exchange_list[num_start:num_end])
            stock_list.append(request_list)
        return stock_list

    @staticmethod
    def load_stock_codes():
        with open(helpers.stock_code_path()) as f:
            return json.load(f)['stock']

    @property
    def all(self):
        warnings.warn('use market_snapshot instead', DeprecationWarning)
        return self.get_stock_data(self.stock_list)

    @property
    def all_market(self):
        """return quotation with stock_code prefix key"""
        return self.get_stock_data(self.stock_list, prefix=True)

    def stocks(self, stock_codes, prefix=False):
        return self.real(stock_codes, prefix)

    def real(self, stock_codes, prefix=False):
        """return specific stocks real quotation
        :param stock_codes: stock code or list of stock code, when prefix is True, stock code must start with sh/sz
        :param prefix: if prefix is True, stock_codes must contain sh/sz market flag.If prefix is False, index quotation can't return
        :return quotation dict, key is stock_code, value is real quotation. If prefix with True, key start with sh/sz market flag

        """
        if type(stock_codes) is not list:
            stock_codes = [stock_codes]

        stock_list = self.gen_stock_list(stock_codes)
        return self.get_stock_data(stock_list, prefix=prefix)

    def market_snapshot(self, prefix=False):
        """return all market quotation snapshot
        :param prefix: if prefix is True, return quotation dict's  stock_code key start with sh/sz market flag
        """
        return self.get_stock_data(self.stock_list, prefix=prefix)

    def get_stocks_by_range(self, params):
        headers = {
            'Accept-Encoding': 'gzip, deflate, sdch',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.100 Safari/537.36'
        }

        r = self._session.get(self.stock_api + params, headers=headers)
        return r.text

    def get_stock_data(self, stock_list, **kwargs):
        pool = ThreadPool(len(stock_list))
        res = pool.map(self.get_stocks_by_range, stock_list)
        return self.format_response_data([x for x in res if x is not None], **kwargs)

    def __del__(self):
        if self._session is not None:
            self._session.close()

    def format_response_data(self, rep_data, **kwargs):
        pass