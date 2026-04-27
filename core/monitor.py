import scrape.health_check
import scrape.details
from datetime import datetime
from core.config import CephConfig, CephState
from core.api_client import CephApiClient
from core.logger import get_logger

# 로그 객체 생성
logger = get_logger("Monitor")

class CephMonitor:
    def __init__(self, config: CephConfig, state: CephState, alert_manager):
        """
        config: 설정값 (불변)
        state: 상태값 (가변)
        alert_manager: 알림 제어 객체 (utils/alert_manager.py)
        """
        self.config = config
        self.state = state
        self.api = CephApiClient(config, state)
        self.alert = alert_manager

    def run_check(self):
        """30초 주기 모니터링 메인 로직"""
        logger.info("Initiate Ceph cluster health check")

        # 1. 인증 및 연결 확인 (성공 시 True, 실패 시 에러 코드 문자열 반환)
        result = self.api.ensure_token()
        
        if result is not True:
            # result가 "AUTH_ERR" 또는 "CONN_ERR"인 경우
            current_severity = result
            logger.error(f"시스템 상태 이상: {current_severity} - 모니터링 중단")
            
            # 상태가 처음 변했을 때만 시스템 에러 알림 전송
            if self.state.last_severity != current_severity:
                msg = "인증 정보(ID/PW)를 확인하세요" if result == "AUTH_ERR" else "네트워크 및 MGR 상태를 확인하세요"
                self.alert.send_error(current_severity, msg)
                self.state.last_severity = current_severity
            return

        # 2. Ceph 클러스터 상태 수집
        try:
            # api_client에서 최신 헤더 가져오기
            headers = self.api.get_headers()
            
            # scrape.health_check.main 인자 매칭 완료
            severity, detail = scrape.health_check.main(
                active_mgr_ip=self.state.active_ip, 
                token_headers=headers
            )
            logger.info(f"클러스터 상태 수집 완료: {severity} ({detail})")

            # 3. 상태 변화 감지 및 복구 알림
            if severity != self.state.last_severity:
                logger.info(f"상태 변화 감지: {self.state.last_severity} -> {severity}")
                
                # 이전 상태가 나빴다가(ERR, WARN, CONN_ERR 등) OK로 돌아온 경우
                if severity == "HEALTH_OK":
                    self.alert.send_resolved()
                
                # 상태 업데이트
                self.state.last_severity = severity

            # 4. 클러스터 경고/에러 발생 시 상세 정보 수집 및 알림
            if severity in ["HEALTH_WARN", "HEALTH_ERR"]:
                # scrape.details.main 인자 매칭 완료
                more_info = scrape.details.main(
                    active_mgr_ip=self.state.active_ip, 
                    token_headers=headers
                )
                self.alert.send_cluster_alert(severity, detail, more_info)

        except Exception as e:
            # 헬스 체크 과정에서 발생하는 예상치 못한 모든 예외 기록
            logger.exception(f"헬스 체크 루프 중 예외 발생: {e}")

    def run_daily_report(self):
        """매일 정해진 시간에 클러스터 상태 요약 전송"""
        logger.info("데일리 리포트 생성 시작")
        
        if self.api.ensure_token():
            try:
                headers = self.api.get_headers()
                # 인자 매칭 수정 (active_mgr_ip, token_headers)
                more_info = scrape.details.main(
                    active_mgr_ip=self.state.active_ip, 
                    token_headers=headers
                )
                self.alert.send_daily_status(self.state.last_severity, more_info)
                logger.info("데일리 리포트 전송 완료")
            except Exception as e:
                logger.error(f"데일리 리포트 생성 실패: {e}")