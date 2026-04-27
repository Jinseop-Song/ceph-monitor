import requests
from .base import BaseNotifier

class SlackNotifierBase(BaseNotifier):
    def _create_payload(self, severity, detail, channel_id, more_info):
        if isinstance(more_info, dict):
            # PG 필터링 (정상이 아닌 것만)
            pg_raw = more_info.get("pg_info_str", "No PG info")
            pg_list = [p.strip() for p in pg_raw.split(',') if p.strip()]
            issue_pgs = [p for p in pg_list if 'active+clean' not in p]
            pg_summary = "✅ *All PGs Healthy*" if not issue_pgs else "⚠️ *Issues:* " + ", ".join(issue_pgs)

            # Top Issues 가공 (빈 줄 제거 및 요약)
            detail_lines = [line.strip() for line in detail.split('\n') if line.strip()]
            short_detail = "\n".join([f"• {line}" for line in detail_lines[:4]])
            has_more = len(detail_lines) > 3

            # 깨지지 않는 바 그래프
            total_gb = int(more_info.get("total_gb", 1))
            used_gb = int(more_info.get("total_used_raw_gb", 0))
            used_per = (used_gb / total_gb * 100) if total_gb > 0 else 0
            bar_cnt = int(used_per / 10)
            capacity_display = f"`{'■' * bar_cnt}{'□' * (10 - bar_cnt)}` *{used_per:.2f}%*"
            osd_status = f"{more_info.get('osd_up_count')} UP / {more_info.get('osd_in_count')} IN"
        else:
            pg_summary = "N/A"; short_detail = str(more_info); osd_status = "N/A"; capacity_display = "N/A"; has_more = False

        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": ":pepe-spin: Ceph Cluster Alert", "emoji": True}},
            {"type": "divider"},
            {"type": "section", "fields": [
                {"type": "mrkdwn", "text": f"*Status:*\n`{severity}`"},
                {"type": "mrkdwn", "text": f"*OSD Status:*\n`{osd_status}`"}
            ]},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Usage:*\n{capacity_display}"}},
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Top Issues:*\n{short_detail}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*PG Health:*\n{pg_summary}"}}
        ]

        if has_more:
            blocks.append({
                "type": "actions",
                "elements": [{
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🔍 대시보드에서 더보기", "emoji": True},
                    "url": "https://10.110.0.105:8443/", # 실제 주소로 수정
                    "style": "primary"
                }]
            })

        blocks.append({"type": "divider"})
        blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": "Powered by Jinseop.song - System Engineering Team, Infra Dept."}]})

        return {"channel": channel_id, "username": "ceph_monitor_bot", "icon_emoji": ":ceph_logo:", "blocks": blocks}

class SlackBotNotifier(SlackNotifierBase):
    def __init__(self, token, channel_id):
        self.token, self.channel_id = token, channel_id
    def send(self, severity, detail, more_info=None):
        url = "https://slack.com/api/chat.postMessage"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        payload = self._create_payload(severity, detail, self.channel_id, more_info)
        requests.post(url, headers=headers, json=payload, timeout=5)

class SlackWebhookNotifier(SlackNotifierBase):
    def __init__(self, url, channel_id):
        self.url, self.channel_id = url, channel_id
    def send(self, severity, detail, more_info=None):
        payload = self._create_payload(severity, detail, self.channel_id, more_info)
        requests.post(self.url, json=payload, timeout=5)