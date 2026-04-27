import configparser
import schedule
import time
import sys
from core.config import CephConfig, CephState
from core.monitor import CephMonitor
from utils.alert_manager import AlertManager
from notifiers import get_notifier
from core.logger import get_logger

# 로그 설정
logger = get_logger("Main")

def load_config(file_path='ceph_monitor.conf'):
    """
    설정 파일을 읽어서 CephConfig 객체를 생성합니다.
    데이터 타입 변환(str -> list, str -> int)을 여기서 처리합니다.
    """
    conf = configparser.ConfigParser()
    try:
        # 파일이 존재하는지 확인
        files_read = conf.read(file_path, encoding='utf-8')
        if not files_read:
            logger.error(f"설정 파일을 찾을 수 없습니다: {file_path}")
            sys.exit(1)

        # 1. Ceph 정보 정제
        mgr_ips = [ip.strip() for ip in conf.get('ceph', 'mgr_ips').split(',')]
        
        # 2. 쿨다운 정보 정제 (정수형 변환)
        cd_cluster = conf.getint('cooldown', 'cluster_alert', fallback=60)
        cd_conn = conf.getint('cooldown', 'conn_err', fallback=30)
        cd_auth = conf.getint('cooldown', 'auth_err', fallback=120)

        # 3. 리프레시 인터벌 정제
        refresh_interval = conf.getint('monitor', 'refresh_interval', fallback=60)

        # 4. CephConfig 객체 조립
        config = CephConfig(
            mgr_ips=mgr_ips,
            username=conf.get('auth', 'username'),
            password=conf.get('auth', 'password'),
            platform=conf.get('webhook', 'platform').lower(),
            webhook_url=conf.get('webhook', 'webhook_url', fallback=None),
            bot_token=conf.get('webhook', 'bot_token', fallback=None),
            channel_id=conf.get('webhook', 'channel_id', fallback=None),
            cd_cluster_min=cd_cluster,
            cd_conn_min=cd_conn,
            cd_auth_min=cd_auth,
            refresh_interval=refresh_interval
        )
        return config

    except Exception as e:
        logger.error(f"설정 파일을 읽는 중 오류 발생: {e}")
        sys.exit(1)

def main():
    logger.info("========================================")
    logger.info("   Ceph Monitoring Service Starting...  ")
    logger.info("========================================")

    # 1. 설정 및 상태 객체 준비
    config = load_config()
    state = CephState()

    # 2. 부품 조립 (Dependency Injection)
    try:
        # 알림 플랫폼 생성 (Slack, MM 등)
        notifier = get_notifier(config)
        
        # 알림 매니저 생성 (쿨다운 제어)
        alert_manager = AlertManager(notifier, config, state)
        
        # 모니터링 엔진 생성
        monitor = CephMonitor(config, state, alert_manager)
        
    except Exception as e:
        logger.error(f"초기화 실패: {e}")
        sys.exit(1)

    # 3. 스케줄링 등록
    # 30초마다 헬스 체크 실행
    schedule.every(config.refresh_interval).seconds.do(monitor.run_check)
    
    # 매일 아침 09:00에 데일리 리포트 실행
    # schedule.every().day.at("09:00").do(monitor.run_daily_report)

    logger.info("서비스가 정상적으로 시작되었습니다.")
    
    # 최초 실행 1회 (30초 기다리기 전에 바로 상태 확인)
    monitor.run_check()

    # 4. 무한 루프
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("사용자 중단 요청으로 종료합니다.")
            break
        except Exception as e:
            logger.error(f"런타임 오류 발생: {e}")
            time.sleep(10) # 에러 시 잠시 대기 후 재시도

if __name__ == "__main__":
    main()