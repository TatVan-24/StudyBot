import os
import json
import uuid
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key
from common.response import success, error
from common.auth import get_user_id

dynamodb = boto3.resource("dynamodb")

TABLE_SESSIONS = os.environ.get("TABLE_SESSIONS", "")
TABLE_SESSION_DOCUMENTS = os.environ.get("TABLE_SESSION_DOCUMENTS", "")
TABLE_DOCUMENTS = os.environ.get("TABLE_DOCUMENTS", "")
TABLE_MESSAGES = os.environ.get("TABLE_MESSAGES", "")

def lambda_handler(event, context):
    try:
        user_id = get_user_id(event)
        if not user_id:
            return error("Missing user identity", 401)

        http_info = event.get("requestContext", {}).get("http", {})
        method = http_info.get("method", "").upper()
        path_params = event.get("pathParameters") or {}
        session_id = path_params.get("id")
        doc_id = path_params.get("doc_id")

        if method == "POST" and not session_id:
            return create_session(event, user_id)
        elif method == "GET" and not session_id:
            return list_sessions(user_id)
        elif method == "GET" and session_id:
            return get_session(user_id, session_id)
        elif method == "POST" and session_id and doc_id:
            return attach_document(user_id, session_id, doc_id)
        elif method == "DELETE" and session_id and doc_id:
            return detach_document(user_id, session_id, doc_id)
        else:
            return error(f"Unsupported route or method: {method}", 400)

    except Exception as e:
        print(f"Error handling session request: {str(e)}")
        return error("Internal server error", 500, str(e))

# 1. POST /sessions — Tạo phiên làm việc mới
def create_session(event, user_id):
    body = {}
    if event.get("body"):
        try:
            body = json.loads(event["body"])
        except Exception:
            body = {}

    title = body.get("title", "New Session")
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    item = {
        "session_id": session_id,
        "user_id": user_id,
        "title": title,
        "document_count": 0,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    table = dynamodb.Table(TABLE_SESSIONS)
    table.put_item(Item=item)

    return success(item, 201)

# 2. GET /sessions — Lấy danh sách session của user (Mới nhất lên đầu)
def list_sessions(user_id):
    table = dynamodb.Table(TABLE_SESSIONS)
    res = table.query(
        IndexName="UserSessions",
        KeyConditionExpression=Key("user_id").eq(user_id),
        ScanIndexForward=False,
    )
    return success({"sessions": res.get("Items", [])})

# 3. GET /sessions/{id} — Lấy chi tiết session + tin nhắn
def get_session(user_id, session_id):
    table_sessions = dynamodb.Table(TABLE_SESSIONS)
    res_sess = table_sessions.get_item(Key={"session_id": session_id})
    session_item = res_sess.get("Item")

    if not session_item:
        return error(f"Session '{session_id}' not found", 404)
    if session_item.get("user_id") != user_id:
        return error("Forbidden: You do not own this session", 403)

    # Lấy danh sách tin nhắn trong session
    table_msgs = dynamodb.Table(TABLE_MESSAGES)
    res_msgs = table_msgs.query(
        KeyConditionExpression=Key("session_id").eq(session_id)
    )

    return success({
        "session": session_item,
        "messages": res_msgs.get("Items", [])
    })

# 4. POST /sessions/{id}/documents/{doc_id} — Gắn document vào session
def attach_document(user_id, session_id, doc_id):
    # Verify ownership session
    table_sessions = dynamodb.Table(TABLE_SESSIONS)
    res_sess = table_sessions.get_item(Key={"session_id": session_id})
    session_item = res_sess.get("Item")
    if not session_item or session_item.get("user_id") != user_id:
        return error("Session not found or forbidden", 403)

    # Verify ownership document
    table_docs = dynamodb.Table(TABLE_DOCUMENTS)
    res_doc = table_docs.get_item(Key={"document_id": doc_id})
    doc_item = res_doc.get("Item")
    if not doc_item or doc_item.get("user_id") != user_id:
        return error("Document not found or forbidden", 403)

    now_iso = datetime.now(timezone.utc).isoformat()
    table_sess_docs = dynamodb.Table(TABLE_SESSION_DOCUMENTS)

    table_sess_docs.put_item(Item={
        "session_id": session_id,
        "document_id": doc_id,
        "attached_at": now_iso,
    })

    # Cập nhật document_count (+1) và updated_at
    table_sessions.update_item(
        Key={"session_id": session_id},
        UpdateExpression="ADD document_count :inc SET updated_at = :u",
        ExpressionAttributeValues={":inc": 1, ":u": now_iso},
    )

    return success({
        "session_id": session_id,
        "document_id": doc_id,
        "attached": True,
        "attached_at": now_iso
    })

# 5. DELETE /sessions/{id}/documents/{doc_id} — Gỡ document khỏi session
def detach_document(user_id, session_id, doc_id):
    table_sessions = dynamodb.Table(TABLE_SESSIONS)
    res_sess = table_sessions.get_item(Key={"session_id": session_id})
    session_item = res_sess.get("Item")
    if not session_item or session_item.get("user_id") != user_id:
        return error("Session not found or forbidden", 403)

    now_iso = datetime.now(timezone.utc).isoformat()
    table_sess_docs = dynamodb.Table(TABLE_SESSION_DOCUMENTS)

    table_sess_docs.delete_item(Key={
        "session_id": session_id,
        "document_id": doc_id
    })

    # Cập nhật updated_at
    table_sessions.update_item(
        Key={"session_id": session_id},
        UpdateExpression="SET updated_at = :u",
        ExpressionAttributeValues={":u": now_iso},
    )

    return success({
        "session_id": session_id,
        "document_id": doc_id,
        "detached": True
    })