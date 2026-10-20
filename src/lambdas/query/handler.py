import os
import json
import uuid
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key
from common.response import success, error
from common.auth import get_user_id

dynamodb = boto3.resource("dynamodb")
sqs_client = boto3.client("sqs")

TABLE_JOBS = os.environ["TABLE_JOBS"]
TABLE_SESSIONS = os.environ["TABLE_SESSIONS"]
TABLE_MESSAGES = os.environ["TABLE_MESSAGES"]
QUEUE_INTERACTIVE_URL = os.environ["QUEUE_INTERACTIVE_URL"]

def lambda_handler(event, context):
    try:
        user_id = get_user_id(event)
        if not user_id:
            return error("Missing user identity", 401)

        http_info = event.get("requestContext", {}).get("http", {})
        method = http_info.get("method", "").upper()
        path = event.get("rawPath", "") or http_info.get("path", "")
        path_params = event.get("pathParameters") or {}
        session_id = path_params.get("id")

        if not session_id:
            return error("Missing session_id path parameter", 400)

        if method == "POST" and "questions" in path:
            return ask_question(event, user_id, session_id)
        elif method == "GET" and "messages" in path:
            return get_messages(user_id, session_id)
        else:
            return error(f"Unsupported route or method: {method} {path}", 400)

    except Exception as e:
        print(f"Error handling query request: {str(e)}")
        return error("Internal server error", 500, str(e))

# 1. POST /sessions/{id}/questions — Gửi câu hỏi, tạo Job QUEUED & gửi SQS Canonical Notification
def ask_question(event, user_id, session_id):
    # Verify session ownership
    table_sessions = dynamodb.Table(TABLE_SESSIONS)
    res_sess = table_sessions.get_item(Key={"session_id": session_id})
    session_item = res_sess.get("Item")
    if not session_item or session_item.get("user_id") != user_id:
        return error("Session not found or forbidden", 403)

    body = {}
    if event.get("body"):
        try:
            body = json.loads(event["body"])
        except Exception:
            body = {}

    # Đọc chuẩn tên field "query" theo contract
    query_text = body.get("query", "").strip()
    if not query_text:
        return error("Query text cannot be empty", 400)

    job_id = f"job_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Ghi Job đầy đủ thông tin vào DynamoDB StudyBotJobs (Source of Truth)
    table_jobs = dynamodb.Table(TABLE_JOBS)
    table_jobs.put_item(Item={
        "job_id": job_id,
        "user_id": user_id,
        "session_id": session_id,
        "job_type": "ANSWER_QUERY",
        "job_version": 1,
        "status": "QUEUED",
        "query": query_text,
        "created_at": now_iso,
        "updated_at": now_iso,
    })

    # Cập nhật updated_at cho Session
    table_sessions.update_item(
        Key={"session_id": session_id},
        UpdateExpression="SET updated_at = :u",
        ExpressionAttributeValues={":u": now_iso},
    )

    # Gửi SQS message chuẩn Canonical Notification (CHỈ CÓ 3 FIELD)
    sqs_client.send_message(
        QueueUrl=QUEUE_INTERACTIVE_URL,
        MessageBody=json.dumps({
            "schema_version": 1,
            "job_id": job_id,
            "job_type": "ANSWER_QUERY",
        }),
    )

    # Trả 202 Accepted
    return success({
        "job_id": job_id,
        "session_id": session_id,
        "status": "QUEUED",
    }, 202)

# 2. GET /sessions/{id}/messages — Lấy lịch sử chat trong Session
def get_messages(user_id, session_id):
    table_sessions = dynamodb.Table(TABLE_SESSIONS)
    res_sess = table_sessions.get_item(Key={"session_id": session_id})
    session_item = res_sess.get("Item")
    if not session_item or session_item.get("user_id") != user_id:
        return error("Session not found or forbidden", 403)

    table_msgs = dynamodb.Table(TABLE_MESSAGES)
    res_msgs = table_msgs.query(
        KeyConditionExpression=Key("session_id").eq(session_id)
    )

    return success({"messages": res_msgs.get("Items", [])})