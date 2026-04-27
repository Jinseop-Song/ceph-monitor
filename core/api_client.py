import requests
import jwt
from datetime import datetime, timedelta
from core.config import CephConfig, CephState
from core.logger import get_logger

# 인증서 경고 무시
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = get_logger("ApiClient")

class CephApiClient:
    def __init__(self, config: CephConfig, state: CephState):
        self.config = config
        self.state = state
        self.session = requests.Session()
        self.session.verify = False

    def ensure_token(self) -> bool:
        """토큰 유효성 확인 및 갱신"""
        if self.state.token:
            try:
                decoded = jwt.decode(self.state.token, options={"verify_signature": False})
                exp_time = datetime.fromtimestamp(decoded.get("exp"))
                
                # 현재 시간이 만료 10분 전보다 이전이면 유효 (부등호 수정 완료)
                if datetime.now() < (exp_time - timedelta(minutes=10)):
                    return True
                logger.info(f"Token is expiring soon (at {exp_time}). Refreshing...")
            except Exception as e:
                logger.error(f"Token decode error: {e}")

        return self._login()

    def _login(self) -> bool:
        """MGR 순회 로그인"""
        payload = {"username": self.config.username, "password": self.config.password}
        headers = {"Accept": "application/vnd.ceph.api.v1.0+json", "Content-Type": "application/json"}

        for ip in self.config.mgr_ips:
            try:
                url = f"https://{ip}:8443/api/auth"
                resp = self.session.post(url, json=payload, headers=headers, timeout=10)

                if resp.status_code == 201:
                    self.state.active_ip = ip
                    self.state.token = resp.json().get('token')
                    logger.info(f"Connected to MGR: {ip}")
                    return True
                
                if resp.status_code in [401,403]:
                    return "AUTH_ERR"
                
            except Exception as e:
                logger.warning(f"MGR {ip} connection failed: {e}")

        self.state.active_ip = None
        self.state.token = None
        return "CONN_ERR"

    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.state.token}",
            "Accept": "application/vnd.ceph.api.v1.0+json"
        }