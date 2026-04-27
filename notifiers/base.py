import json
from abc import ABC, abstractmethod

class BaseNotifier(ABC):
    @abstractmethod
    def send(self, severity, detail, more_info=None):
        pass

    def format_more_info(self, more_info):
        """딕셔너리 데이터를 슬랙/매터모스트 코드블록 형태로 변환"""
        if isinstance(more_info, dict):
            return f"```json\n{json.dumps(more_info, indent=2, ensure_ascii=False)}\n```"
        return str(more_info) if more_info else "No additional details."