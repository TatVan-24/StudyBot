import os
import json
import uuid
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key
from common.response import success, error
from common.auth import get_user_id

dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")
sqs_client = boto3.client("sqs")

TABLE_DOCUMENTS = os.environ.get("TABLE_DOCUMENTS", "")
TABLE_JOBS = os.environ.get("TABLE_JOBS", "")
BUCKET_DOCUMENT = os.environ.get("BUCKET_DOCUMENT", "")
QUEUE_DOCUMENT_URL = os.environ.get("QUEUE_DOCUMENT_URL", "")

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}

def lambda_handler(event, context):
    try:
        user_id = get_user_id(event)
        if not user_id:
            return error("Missing user identity", 401)

        http_info = event.get("requestContext", {}).get("http", {})
        method = http_info.get("method", "").upper()
        path = event.get("rawPath", "") or http_info.get("path", "")
        document_id = (event.get("pathParameters") or {}).get("id")

        if method == "POST" and path.endswith("/uploads"):
            return create_upload(event, user_id)
        elif method == "GET" and not document_id:
            return list_documents(user_id)
        elif method == "GET" and document_id:
            return get_document(user_id, document_id)
        elif method == "DELETE" and document_id:
            return delete_document(user_id, document_id)
        else:
            return error(f"Unsupported route or method: {method} {path}", 400)

    except Exception as e:
        print(f"Error handling document request: {str(e)}")
        return error("Internal server error", 500, str(e))

# 1. POST /documents/uploads - Tạo S3 Presigned POST URL & Bản ghi PENDING
def create_upload(event, user_id):
    body = {}
    if event.get("body"):
        try:
            body = json.loads(event["body"])
        except Exception:
            body = {}

    filename = body.get("filename", "document.pdf")
    content_type = body.get("content_type", "application/pdf")

    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return error(f"Invalid file type '{ext}'. Allowed: .pdf, .txt, .md", 400)

    document_id = f"doc_{uuid.uuid4().hex[:12]}"
    s3_key = f"uploads/{user_id}/{document_id}/{filename}"
    now_iso = datetime.now(timezone.utc).isoformat()

    table = dynamodb.Table(TABLE_DOCUMENTS)
    doc_item = {
        "document_id": document_id,
        "user_id": user_id,
        "filename": filename,
        "s3_bucket": BUCKET_DOCUMENT,
        "s3_key": s3_key,
        "content_type": content_type,
        "status": "UPLOADING",
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    table.put_item(Item=doc_item)

    # Sinh S3 Presigned POST URL (Thời hạn 300s = 5 phút, giới hạn 10MB)
    presigned = s3_client.generate_presigned_post(
        Bucket=BUCKET_DOCUMENT,
        Key=s3_key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", 1, 10 * 1024 * 1024],
        ],
        ExpiresIn=300,
    )

    return success({
        "document_id": document_id,
        "filename": filename,
        "upload_url": presigned["url"],
        "fields": presigned["fields"],
        "s3_key": s3_key,
        "status": "UPLOADING",
        "expires_in_seconds": 300,
    }, 201)

# 2. GET /documents - Danh sách tài liệu của User
def list_documents(user_id):
    table = dynamodb.Table(TABLE_DOCUMENTS)
    res = table.query(
        IndexName="UserDocuments",
        KeyConditionExpression=Key("user_id").eq(user_id),
        ScanIndexForward=False,
    )
    # Filter loại bỏ các tài liệu đã bị DELETE_QUEUED
    items = [doc for doc in res.get("Items", []) if doc.get("status") != "DELETE_QUEUED"]
    return success({"documents": items})

# 3. GET /documents/{id} - Chi tiết 1 tài liệu
def get_document(user_id, document_id):
    table = dynamodb.Table(TABLE_DOCUMENTS)
    res = table.get_item(Key={"document_id": document_id})
    item = res.get("Item")

    if not item:
        return error(f"Document '{document_id}' not found", 404)
    if item.get("user_id") != user_id:
        return error("Forbidden: You do not own this document", 403)

    return success({"document": item})

# 4. DELETE /documents/{id} - Chuyển status DELETE_QUEUED & Gửi SQS Job xóa
def delete_document(user_id, document_id):
    table_docs = dynamodb.Table(TABLE_DOCUMENTS)
    res = table_docs.get_item(Key={"document_id": document_id})
    item = res.get("Item")

    if not item:
        return error(f"Document '{document_id}' not found", 404)
    if item.get("user_id") != user_id:
        return error("Forbidden: You do not own this document", 403)

    now_iso = datetime.now(timezone.utc).isoformat()
    job_id = f"job_{uuid.uuid4().hex[:12]}"

    # Chuyển status sang DELETE_QUEUED trong DynamoDB
    table_docs.update_item(
        Key={"document_id": document_id},
        UpdateExpression="SET #s = :s, updated_at = :u",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": "DELETE_QUEUED", ":u": now_iso},
    )

    # Tạo bản ghi Job xóa trong DynamoDB
    table_jobs = dynamodb.Table(TABLE_JOBS)
    table_jobs.put_item(Item={
        "job_id": job_id,
        "user_id": user_id,
        "job_type": "DELETE_DOCUMENT",
        "status": "QUEUED",
        "document_id": document_id,
        "s3_key": item.get("s3_key"),
        "created_at": now_iso,
        "updated_at": now_iso,
    })

    # Gửi Message vào SQS Queue cho Worker xóa Vector + S3 file
    if QUEUE_DOCUMENT_URL:
        try:
            sqs_client.send_message(
                QueueUrl=QUEUE_DOCUMENT_URL,
                MessageBody=json.dumps({
                    "job_id": job_id,
                    "job_type": "DELETE_DOCUMENT",
                    "user_id": user_id,
                    "document_id": document_id,
                    "s3_key": item.get("s3_key"),
                }),
            )
        except Exception as sqs_err:
            print(f"Warning: Failed to send SQS message: {str(sqs_err)}")

    return success({
        "document_id": document_id,
        "job_id": job_id,
        "status": "DELETE_QUEUED",
        "message": "Document deletion queued successfully"
    })
    #### CI/CD deployment test