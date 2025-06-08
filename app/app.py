import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Form
import json
import redis
import httpx
import logging

app = FastAPI()
r = redis.Redis(host="10.13.13.2", port=30204, decode_responses=True)


@app.post("/slack/interact")
async def slack_interact(payload: str = Form(...)):
    data = json.loads(payload)
    action, task_id = data["actions"][0]["value"].split("|")
    user = data["user"]["username"]
    logging.warning(f"{user} chọn {action} task_id {task_id}")

    if action == "approve":
        r.set(task_id, "approved")
    elif action == "reject":
        r.set(task_id, "rejected")

    response_url = data["response_url"]
    async with httpx.AsyncClient() as client:
        await client.post(
            response_url,
            json={"text": f"✅ {user} choose: {action}", "replace_original": False},
        )

    return {"text": f"✅ You choose: {action}"}


@app.post("/")
async def slack_events(request: Request):
    data = await request.json()
    
    if "challenge" in data:
        return JSONResponse(content={"challenge": data["challenge"]})

    print("Slack event received:", data)

    return JSONResponse(status_code=200, content={})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=80, reload=True, log_level="debug")
