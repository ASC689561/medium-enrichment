# bot.py
import logging
import praw
import time
import redis
from openai import OpenAI
import pandas as pd
import rich
import dotenv
from approval_request import ask_for_approval, wait_for_approval, send_message
import os

dotenv.load_dotenv()

# Cấu hình Reddit API
reddit = praw.Reddit(
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    username=os.environ["REDDIT_USERNAME"],
    password=os.environ["REDDIT_PASSWORD"],
    user_agent=os.environ["REDDIT_USER_AGENT"],
)

client = OpenAI(api_key=os.environ["OPENAI_KEY"])

df = pd.read_excel("./posts.xls")
r = redis.Redis(host="10.13.13.2", port=30204, decode_responses=True)

send_message("Started bot ")


def check_should_reply(text):
    response = client.responses.create(
        model="gpt-4.1",
        input=f"""With the Reddit post title "{text}", should I post the link to the article "Use MT5 in Linux with Docker and Python"? Just answer yes or no.""",
    )
    rich.print(text, " ==> ", response.output_text)
    return "có" in response.output_text.lower()


def generate_reply(title):
    post_titles = list(df["Title"].values)
    response = client.responses.create(
        model="gpt-4.1",
        input=f"""Given the Reddit post title "{title}" and this list of article titles: {post_titles}, should I choose one to share?
If yes, reply with the article title only.
If no, just reply no.""",
    )
    selected = response.output_text
    if selected.lower().strip() in ["no.", "no"]:
        rich.print(f"[red]{title}")
        return
    df_selected = df[df["Title"] == selected.strip("'\"*")]

    if len(df_selected) == 0:
        rich.print("Not found", selected)
        None
    rich.print(f"[green]{title} [blue]{selected}")
    post = df_selected.iloc[0]["Link"]
    title_post = df_selected.iloc[0]["Title"]
    response = client.responses.create(
        model="gpt-4.1",
        input=f"""With the Reddit post title "{title}" and my article titled "{title_post}", write only a 30-word English comment that cleverly includes the link to "{post}". Do not add an introduction or explanation""",
    )
    text = response.output[0].content[0].text
    return text


subreddits = [
    "quant",
    "algotrading",
    "quantresearch",
    "Trading",
    "datascience",
    "TradingView",
    "Entrepreneur",
]


def run_bot():
    for submission in reddit.subreddit("+".join(subreddits)).stream.submissions(
        skip_existing=True
    ):
        try:
            title = submission.title
            try:
                body = generate_reply(title)
            except:
                logging.exception("Error when generate reply", exc_info=True)
                body = None
            if body is None:
                continue

            rich.print(f"{title}")
            rich.print(f"[green]{body}")
            task_id = submission.id
            try:
                ask_for_approval(task_id, title, body)

                status = wait_for_approval(task_id)
            except:
                status = "rejected"

            if status == "approved" or status == "auto":
                submission.reply(body)
                print(f"[+] Commented to: {submission.id}")
            elif status == "rejected":
                print(f"[!] Rejected by admin for: {submission.id}")
            else:
                print(f"[!] Timeout waiting approval for: {submission.id}")
            send_message("Reply done: " + str(e))
            time.sleep(15)
        except Exception as e:
            print(f"[!] Error: {e}")
            send_message("Reply error: " + str(e))
            time.sleep(60)


if __name__ == "__main__":
    while True:
        try:
            run_bot()
        except KeyboardInterrupt:
            break
        except:
            logging.exception("Error when fetch data", exc_info=True)
            time.sleep(120)
