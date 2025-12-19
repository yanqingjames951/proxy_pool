# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     ProxyHandler.py
   Description :
   Author :       JHao
   date：          2016/12/3
-------------------------------------------------
   Change Activity:
                   2016/12/03:
                   2020/05/26: 区分http和https
-------------------------------------------------
"""
__author__ = 'JHao'

from helper.proxy import Proxy
from db.dbClient import DbClient
from handler.configHandler import ConfigHandler


class ProxyHandler(object):
    """ Proxy CRUD operator"""

    def __init__(self):
        self.conf = ConfigHandler()
        self.db = DbClient(self.conf.dbConn)
        self.db.changeTable(self.conf.tableName)

    def get(self, https=False):
        """
        return a proxy
        Args:
            https: True/False
        Returns:
        """
        proxy = self.db.get(https)
        return Proxy.createFromJson(proxy) if proxy else None

    def pop(self, https):
        """
        return and delete a useful proxy
        :return:
        """
        proxy = self.db.pop(https)
        if proxy:
            return Proxy.createFromJson(proxy)
        return None

    def getBatch(self, count=10, https=False, region=None):
        """
        return multiple proxies at once
        Args:
            count: number of proxies to return (max 100)
            https: True/False
            region: filter by region (optional)
        Returns:
            list of Proxy objects
        """
        count = min(count, 100)  # 限制最大数量
        all_proxies = self.db.getAll(https)
        proxies = [Proxy.createFromJson(p) for p in all_proxies]
        
        # 按地区过滤
        if region:
            proxies = [p for p in proxies if region.lower() in (p.region or '').lower()]
        
        # 按延迟排序（延迟小的优先）
        proxies = sorted(proxies, key=lambda x: x.latency if x.latency > 0 else 999999)
        
        return proxies[:count]

    def put(self, proxy):
        """
        put proxy into use proxy
        :return:
        """
        self.db.put(proxy)

    def delete(self, proxy):
        """
        delete useful proxy
        :param proxy:
        :return:
        """
        return self.db.delete(proxy.proxy)

    def deleteBatch(self, proxies):
        """
        delete proxies in batch
        :param proxies: list of proxy str
        :return:
        """
        for proxy in proxies:
            self.db.delete(proxy)
        return True

    def getAll(self, https=False):
        """
        get all proxy from pool as Proxy list
        :return:
        """
        proxies = self.db.getAll(https)
        return [Proxy.createFromJson(_) for _ in proxies]

    def exists(self, proxy):
        """
        check proxy exists
        :param proxy:
        :return:
        """
        return self.db.exists(proxy.proxy)

    def getCount(self):
        """
        return raw_proxy and use_proxy count
        :return:
        """
        total_use_proxy = self.db.getCount()
        return {'count': total_use_proxy}
