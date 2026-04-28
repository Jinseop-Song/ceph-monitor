from .slack import SlackWebhookNotifier,SlackBotNotifier
# from .mattermost import MattermostNotifier

def get_notifier(config):
    p = config.platform.lower()

    if p == "slack":
        if config.bot_token:
            return SlackBotNotifier(config.bot_token, config.channel_id)
        if config.webhook_url:
            return SlackWebhookNotifier(config.webhook_url, config.channel_id)
        else:
            raise ValueError("Slack 설정에 (token+channel) 또는 (webhook_url)이 필요합니다.")

    # 매터모스트는 잠시 비활성화
    elif p == "mattermost":
        raise ValueError("Mattermost 모듈은 현재 임시로 비활성화되어 있습니다. slack을 사용하세요.")

    else:
        raise ValueError(f"지원하지 않는 플랫폼입니다: {p}")