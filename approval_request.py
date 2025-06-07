import requests
import time

import os
import dotenv
import redis

dotenv.load_dotenv()


r = redis.Redis(host="10.13.13.2", port=30204, decode_responses=True)
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
CHANNEL_ID = os.environ["SLACK_CHANNEL_ID"]
print(SLACK_BOT_TOKEN, CHANNEL_ID)


def send_message(message):
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-type": "application/json",
    }
    data = {
        "channel": CHANNEL_ID,
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message},
            }
        ],
    }

    response = requests.post(
        "https://slack.com/api/chat.postMessage", json=data, headers=headers
    )


def ask_for_approval(task_id, title, body):

    SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
    CHANNEL_ID = os.environ["SLACK_CHANNEL_ID"]
    print(SLACK_BOT_TOKEN, CHANNEL_ID)

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-type": "application/json",
    }

    data = {
        "channel": CHANNEL_ID,
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": title, "emoji": True},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": body},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve"},
                        "style": "primary",
                        "value": f"approve|{task_id}",
                        "action_id": "approve_button",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Reject"},
                        "style": "danger",
                        "value": f"reject|{task_id}",
                        "action_id": "reject_button",
                    },
                ],
            },
        ],
    }

    response = requests.post(
        "https://slack.com/api/chat.postMessage", json=data, headers=headers
    )
    print(response.json())
    r.set(task_id, "pending")


def wait_for_approval(task_id, timeout=1e6):
    try:
        for _ in range(int(timeout)):
            status = r.get(task_id)
            if status and status != "pending":
                return status
            time.sleep(1)
        return "timeout"
    finally:
        r.delete(task_id)


# ask_for_approval("id_1", "Do you want to approve request ***", "xxx")
# print(wait_for_approval("id_1"))
