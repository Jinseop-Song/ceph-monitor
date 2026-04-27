from datetime import datetime, timedelta
from core.config import CephConfig, CephState
from core.logger import get_logger

logger = get_logger("AlertManager")

class AlertManager:
    def __init__(self, notifier, config: CephConfig, state: CephState):
        """
        config에서 설정된 쿨다운 값을 가져와 사용합니다.
        """
        self.notifier = notifier
        self.config = config
        self.state = state
        
        # 설정값 매핑
        self.cooldown_map = {
            "CLUSTER_ALERT": self.config.cd_cluster,
            "CONN_ERR": self.config.cd_conn,
            "AUTH_ERR": self.config.cd_auth
        }

    def _should_send(self, alert_type: str) -> bool:
        last_time = self.state.last_alert_times.get(alert_type)
        if not last_time:
            return True

        # config 객체에 정의된 '분' 단위를 가져옴
        if alert_type == "CLUSTER_ALERT":
            cooldown_min = self.config.cd_cluster_min
        elif alert_type == "AUTH_ERR":
            cooldown_min = self.config.cd_auth_min
        else: # CONN_ERR
            cooldown_min = self.config.cd_conn_min

        # 실제 계산
        if datetime.now() - last_time > timedelta(minutes=cooldown_min):
            return True
        return False

    def send_cluster_alert(self, severity, detail, more_info):
        if self._should_send("CLUSTER_ALERT"):
            logger.info(f"클러스터 알림 전송: {severity}")
            self.notifier.send(severity, detail, more_info)
            self.state.last_alert_times["CLUSTER_ALERT"] = datetime.now()

    def send_resolved(self):
        """복구 알림은 쿨다운 없이 전송 후 모든 기록 초기화"""
        logger.info("복구 알림 전송: HEALTH_OK")
        self.notifier.send("OK", "CEPH_RESOLVED", "클러스터 상태가 복구되었습니다.")
        self.state.last_alert_times.clear()

    def send_error(self, err_type, msg):
        """시스템 에러 (CONN_ERR, AUTH_ERR)"""
        if self._should_send(err_type):
            logger.info(f"시스템 에러 전송: {err_type}")
            self.notifier.send("SYSTEM_ERR", err_type, msg)
            self.state.last_alert_times[err_type] = datetime.now()

    def send_daily_status(self, severity, more_info):
        """데일리 리포트는 쿨다운 상관없이 무조건 전송"""
        self.notifier.send(severity, "DAILY_REPORT", more_info)