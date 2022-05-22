from wsgiref import headers
import requests

class HTTPClient:
    def __init__(self, headers_dict: dict) -> None:
        self.headers_dict = headers_dict

    def get(self, url) -> requests.Response:
        return requests.get(url=url, headers=self.headers_dict)