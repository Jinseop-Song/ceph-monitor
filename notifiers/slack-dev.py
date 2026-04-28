import requests
import io
from .base import BaseNotifier

class SlackNotifierBase(BaseNotifier):
    """페이로드 블록킷을 생성하는 베이스 클래스"""
    def _create_payload(self, severity, detail, channel_id, more_info):
        if isinstance(more_info, dict):
            # 1. PG 필터링 (정상이 아닌 것만 요약)
            pg_raw = more_info.get("pg_info_str", "No PG info")
            pg_list = [p.strip() for p in pg_raw.split(',') if p.strip()]
            issue_pgs = [p for p in pg_list if 'active+clean' not in p]
            pg_summary = "✅ *All PGs Healthy*" if not issue_pgs else "⚠️ *Issues:* " + ", ".join(issue_pgs)

            # 2. Top Issues 가공 (알람창에는 핵심 3개만 요약 노출)
            detail_lines = [line.strip() for line in detail.split('\n') if line.strip()]
            short_detail = "\n".join([f"• {line}" for line in detail_lines[:3]])
            
            # 3. 용량 바 그래프
            total_gb = int(more_info.get("total_gb", 1))
            used_gb = int(more_info.get("total_used_raw_gb", 0))
            used_per = (used_gb / total_gb * 100) if total_gb > 0 else 0
            bar_cnt = int(used_per / 10)
            capacity_display = f"`{'■' * bar_cnt}{'□' * (10 - bar_cnt)}` *{used_per:.2f}%*"
            osd_status = f"{more_info.get('osd_up_count')} UP / {more_info.get('osd_in_count')} IN"
        else:
            pg_summary = "N/A"; short_detail = str(more_info); osd_status = "N/A"; capacity_display = "N/A"

        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": "🚨 Ceph Cluster Alert", "emoji": True}},
            {"type": "divider"},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*Status:*\n`{severity}`"},
                {"type": "mrkdwn", "text": f"*OSD Status:*\n`{osd_status}`"}
            ]},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Usage:*\n{capacity_display}"}},
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Top Issues:*\n{short_detail}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*PG Health Summary:*\n{pg_summary}"}},
            {"type": "divider"},
            {"type": "context", "elements": [
                {"type": "mrkdwn", "text": "Powered by Jinseop.song"}
            ]}
        ]

        return {"channel": channel_id, "username": "ceph_monitor_bot", "icon_emoji": ":ceph_logo:", "blocks": blocks}
    
class SlackBotNotifier(SlackNotifierBase):
    def __init__(self, token, channel_id):
        self.token, self.channel_id = token, channel_id
    def send(self, severity, detail, more_info=None):
        url = "https://slack.com/api/chat.postMessage"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        payload = self._create_payload(severity, detail, self.channel_id, more_info)
        bot_request = requests.post(url, headers=headers, json=payload, timeout=10)

        # [2] 전송 성공 시 스레드 답글 달기
        if bot_request.status_code == 200 and more_info:
            parent_ts = bot_request.json().get("ts") # 부모 메시지의 타임스탬프 ID
            
            # 헬스 로그 및 OSD DF 원본 데이터 추출 (Scraper에서 담아줘야 함)
            health_log = more_info.get("health_detail_raw", "상세 헬스 로그 데이터가 없습니다.")
            osd_df_log = more_info.get("osd_df_raw", "상세 OSD DF 데이터가 없습니다.")

            # 슬랙 메시지 글자 수 제한(약 4000자)을 고려하여 안전하게 슬라이싱
            # 코드 블록(```)을 사용해 가독성 확보
            thread_text = (
                f"📄 *Ceph Health Detail Full Log*\n"
                f"{health_log}\n"
                f"{osd_df_log}")

            thread_payload = {
                "channel": self.channel_id,
                "thread_ts": parent_ts,
                "text": thread_text
            }

            # 원문 TS 기반으로 쓰레드 전송
            requests.post(url, headers=headers, json=thread_payload, timeout=10)

class SlackWebhookNotifier(SlackNotifierBase):
    def __init__(self, url, channel_id):
        self.url, self.channel_id = url, channel_id

    
    def send(self, severity, detail, more_info=None):
        payload = self._create_payload(severity, detail, self.channel_id, more_info)
        webhook_request = requests.post(self.url, json=payload, timeout=10)

        if webhook_request.status_code == 200 and more_info:
            # 헬스 로그 및 OSD DF 원본 데이터 추출
            health_log = more_info.get("health_detail_raw", "상세 헬스 로그 데이터가 없습니다.")
            osd_df_log = more_info.get("osd_df_raw", "상세 OSD DF 데이터가 없습니다.")

            # --- 2-1. Health Detail 블록킷 전송 ---
            health_payload = {
                "channel": self.channel_id,
                "username": "ceph_monitor_bot",
                "icon_emoji": ":ceph_logo:",
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": "Ceph Health Details", "emoji": True}
                    },
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"```\n{health_log}\n```"}
                    },
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"```\n{osd_df_log}\n```"}
                    }
                ]
            }

            requests.post(self.url, json=health_payload, timeout=10)