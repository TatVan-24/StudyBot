import os
import json
import uuid
import urllib.parse
from datetime import datetime, timezone
import boto3

dynamodb = boto3.resource("dynamodb")
sqs_client = boto3.client("sqs")

TABLE_DOCUMENTS = os.environ.get("TABLE_DOCUMENTS")
TABLE_JOBS = os.environ.get("TABLE_JOBS")
QUEUE_DOCUMENT_URL = os.environ.get("QUEUE_DOCUMENT_URL")

def lambda_handler(event, context):
    try:
        table_docs = dynamodb.Table(TABLE_DOCUMENTS)
        table_jobs = dynamodb.Table(TABLE_JOBS)

        for record in event.get("Records", []):
            if "s3" not in record:
                continue

            bucket = record["s3"]["bucket"]["name"]
            key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
            
            print(f"Processing s3://{bucket}/{key}")

            # key format: "uploads/{user_id}/{document_id}/{filename}"
            parts = key.split("/")
            if len(parts) < 4 or parts[0] != "uploads":
                print(f"Invalid key format: {key}")
                continue
                
            user_id = parts[1]
            document_id = parts[2]
            
            # Fetch document từ DynamoDB
            res = table_docs.get_item(Key={"document_id": document_id})
            item = res.get("Item")
            
            if not item:
                print(f"Document not found: {document_id}")
                continue
                
            current_status = item.get("status")
            # Idempotency check
            if current_status in ["INGEST_QUEUED", "PROCESSING", "ACTIVE", "DELETE_QUEUED", "DELETED"]:
                print(f"Document already in terminal/queued state: {current_status} for {document_id}")
                continue
                
            if current_status != "UPLOADING":
                print(f"Unexpected document status: {current_status} for {document_id}")
                continue

            now_iso = datetime.now(timezone.utc).isoformat()
            
            # 1. Cập nhật status document
            table_docs.update_item(
                Key={"document_id": document_id},
                UpdateExpression="SET #s = :s, updated_at = :u",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":s": "INGEST_QUEUED",
                    ":u": now_iso,
                },
            )
            print(f"Document {document_id} status updated to INGEST_QUEUED")
            
            # 2. Tạo Job
            job_id = f"job_{uuid.uuid4().hex[:12]}"
            table_jobs.put_item(Item={
                "job_id": job_id,
                "user_id": user_id,
                "document_id": document_id,
                "job_type": "INGEST_DOCUMENT",
                "job_version": 1,
                "status": "QUEUED",
                "created_at": now_iso,
                "updated_at": now_iso,
            })
            print(f"Job {job_id} created and queued")
            
            # 3. Gửi SQS message
            sqs_client.send_message(
                QueueUrl=QUEUE_DOCUMENT_URL,
                MessageBody=json.dumps({
                    "schema_version": 1,
                    "job_id": job_id,
                    "job_type": "INGEST_DOCUMENT",
                }),
            )
            print(f"Message sent to SQS for job {job_id}")

        return {"statusCode": 200, "body": "OK"}
    except Exception as e:
        print(f"Error processing S3 event: {e}")
        return {"statusCode": 500, "body": "Error"}