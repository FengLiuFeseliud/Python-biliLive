import requests


class Link:

    # 通用请求头
    bilibili_headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        "Referer": "https://live.bilibili.com/",
        'cookie': '',
        'User-Agen': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
    }

    encoding = "utf-8"

    def __init__(self, headers):
        self.headers = headers if headers != None else self.bilibili_headers
        self.code = 200

    def _cookie_key(self, key):
        cookie_key_ = {}
        for key_ in self.headers["cookie"].split('; '):
            key_data = key_.split("=")
            if key.count(key_data[0]) != 0:
                if len(key) == 1:
                    return key_data[1]
                cookie_key_[key_data[0]] = key_data[1]

        return cookie_key_

    def _link(self, api, data={}, json=True, mode="GET"):
        if mode == "GET":
            with requests.get(api, data=data, headers=self.headers) as req:
                self.code = req.status_code
                req.encoding = self.encoding
                requests_data = req.json() if json else req.text
        elif mode == "POST":
            with requests.post(api, data=data, headers=self.headers) as req:
                self.code = req.status_code
                req.encoding = self.encoding
                requests_data = req.json() if json else req.text
        return requests_data