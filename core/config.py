from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime

@dataclass(frozen=True)
class CephConfig:
    # 1. Ceph 접속 정보
    mgr_ips: List[str]
    username: str
    password: str
    
    # 2. 알림 플랫폼 정보
    platform: str
    
    # 3. 알림 상세 정보 (Mattermost/Slack 공용)
    webhook_url: Optional[str] = None
    bot_token: Optional[str] = None
    channel_id: Optional[str] = None
    
    # 4. 쿨다운 설정 (Main.py에서 던지는 변수명과 일치)
    cd_cluster_min: int = 60
    cd_conn_min: int = 30
    cd_auth_min: int = 120

    # 5. Refresh interval 설정
    refresh_interval: int = 60

@dataclass
class CephState:
    active_ip: Optional[str] = None
    token: Optional[str] = None
    last_severity: str = "HEALTH_OK"
    last_alert_times: Dict[str, datetime] = field(default_factory=dict)