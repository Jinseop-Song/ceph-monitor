import requests
from .base import BaseNotifier

class MattermostNotifier(BaseNotifier):  # 이 이름이 __init__.py에서 부르는 이름과 똑같아야 함!
    def __init__(self, url):
        self.url = url
    # ... (생략)