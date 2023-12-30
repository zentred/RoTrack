import threading, time, requests
from itertools import cycle
from collections import deque, Counter

class ProxyPool:
    def __init__(self, proxies):
        self.raw_proxies = proxies
        self.alive_proxies = []
        self.dead_proxies = []
        threading.Thread(target=self.retry).start()

    def retry(self):
        while 1:
            for proxy in self.dead_proxies:
                self.put(proxy)
            self.dead_proxies = []
            time.sleep(30)
    
    def get(self):
        if len(self.raw_proxies):
            return self.raw_proxies.pop()
        return self.alive_proxies.pop()

    def put(self, proxy):
        self.alive_proxies.insert(0, proxy)

    def remove(self, proxy):
        self.dead_proxies.append(proxy)
