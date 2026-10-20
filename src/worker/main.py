import json
import time
import uuid
from decimal import Decimal 
from datetime import datetime, timezone
import boto3

from src.worker.config import (
    AWS_REGION, QUEUE_DOCUMENT_URL, QUEUE_INTERACTIVE_URL,
    TABLE_JOBS, TABLE_DOCUMENTS, TABLE_MESSAGES,
    SQLITE_PATH, EMBEDDING_MODEL
)
from src.worker.logger import log_info, log_warn, log_error
from src.worker.ingest import ingest_document
from src.worker.session_store import WorkerSessionStore
from src.rag_pipeline.indexer.embedding import EmbeddingEngine
from src.rag_pipeline.indexer.vector_store import SQLiteVectorStore
from src.rag_pipeline.llm.handlers import handle_query
from src.rag_pipeline.llm.adapters.factory import make_ai, make_vector

# --- INGEST JOB (Giữ nguyên) ---
def _handle_ingest_job(job, dynamodb, s3_client, embedder, store) -> bool:
    # (Giữ nguyên code cũ của bạn, không sửa gì)
    job_id = job["job_id"]
    document_id = job["document_id"]
    user_id = job.get("user_id")
    docs_table = dynamodb.Table(TABLE_DOCUMENTS)
    jobs_table = dynamodb.Table(TABLE_JOBS)
    
    res = docs_table.get_item(Key={"document_id": document_id})
    doc = res.get("Item")
    if not doc: return True

    if doc.get("status") == "ACTIVE":
        log_warn("document_already_active", document_id=document_id)
        jobs_table.update_item(
            Key={"job_id": job_id}, UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={"#s": "status"}, ExpressionAttributeValues={":s": "COMPLETED"}
        )
        return True

    s3_key = doc.get("s3_key") or f"uploads/{user_id}/{document_id}/{doc.get('filename')}"
    result = ingest_document(document_id, s3_key, s3_client, embedder, store, user_id)
    
    now_iso = datetime.now(timezone.utc).isoformat()
    docs_table.update_item(Key={"document_id": document_id}, UpdateExpression="SET #s = :s, updated_at = :u", ExpressionAttributeNames={"#s": "status"}, ExpressionAttributeValues={":s": "ACTIVE", ":u": now_iso})
    jobs_table.update_item(Key={"job_id": job_id}, UpdateExpression="SET #s = :s, #r = :r, updated_at = :u", ExpressionAttributeNames={"#s": "status", "#r": "result"}, ExpressionAttributeValues={":s": "COMPLETED", ":r": {"chunk_count": result["chunk_count"]}, ":u": now_iso})
    log_info("job_completed", job_id=job_id)
    return True


# --- ANSWER JOB (Viết mới hoàn toàn) ---
def _handle_answer_job(job, dynamodb, ai_client, userstore, vector_store) -> bool:
    job_id = job["job_id"]
    user_id = job["user_id"]
    session_id = job["session_id"]
    query_text = job["query"]
    
    log_info("answer_started", job_id=job_id, session_id=session_id)

    try:
        # 1. Gọi RAG pipeline (đã fix bẫy 1 ở ngoài hàm main)
        result = handle_query(
            session_id=session_id,
            user_id=user_id,
            query=query_text,
            ai_client=ai_client,
            userstore=userstore,
            vector_store=vector_store,
            vector_backend="local",
            bedrock_kb_id=""
        )
        
        metadata = result.get("metadata", {})
        now_iso = datetime.now(timezone.utc).isoformat()

        metadata = json.loads(json.dumps(metadata), parse_float=Decimal)

        # 2. Lưu câu trả lời vào bảng Messages
        messages_table = dynamodb.Table(TABLE_MESSAGES)
        msg_id = f"msg_{uuid.uuid4().hex[:8]}"
        messages_table.put_item(Item={
            "session_id": session_id,
            "message_id": msg_id,             # <--- SỬA Ở ĐÂY (thay vì created_at#message_id)
            "created_at": now_iso,            # <--- Thêm created_at riêng
            "query": query_text,
            "answer": metadata.get("answer", ""),
            "status": metadata.get("status", "unknown"),
            "citations": metadata.get("citations", [])
        })

        # 3. Cập nhật Job -> COMPLETED
        jobs_table = dynamodb.Table(TABLE_JOBS)
        jobs_table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #s = :s, #r = :r, updated_at = :u",
            ExpressionAttributeNames={"#s": "status", "#r": "result"},
            ExpressionAttributeValues={
                ":s": "COMPLETED", 
                ":r": metadata, # Bây giờ metadata đã toàn là Decimal, lưu không bị lỗi nữa
                ":u": now_iso
            }
        )
        log_info(
            "answer_completed", 
            job_id=job_id, 
            status=metadata.get("status"), 
            reason=metadata.get("reason", "No reason provided")  # <--- Thêm dòng này
        )
        return True

    except Exception as e:
        log_error("answer_failed", job_id=job_id, error=str(e))
        return False

# --- PROCESS MESSAGE (Router) ---
def _process_message(message, queue_url, sqs, dynamodb, s3_client, embedder, store, ai_client, userstore, vector_store) -> bool:
    try:
        body = json.loads(message["Body"])
        job_id = body.get("job_id", "")
        job_type = body.get("job_type", "")
        
        jobs_table = dynamodb.Table(TABLE_JOBS)
        job = jobs_table.get_item(Key={"job_id": job_id}).get("Item")
        if not job: return True

        if job_type == "INGEST_DOCUMENT":
            return _handle_ingest_job(job, dynamodb, s3_client, embedder, store)
        elif job_type == "ANSWER_QUERY":
            return _handle_answer_job(job, dynamodb, ai_client, userstore, vector_store)
        else:
            log_warn("unsupported_job", job_type=job_type)
            return True
    except Exception as e:
        log_error("process_failed", error=str(e))
        return False

# --- MAIN (Khởi tạo và chạy) ---
def main():
    log_info("worker_starting")
    sqs = boto3.client("sqs", region_name=AWS_REGION)
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    s3_client = boto3.client("s3", region_name=AWS_REGION)
    
    embedder = EmbeddingEngine(model_name=EMBEDDING_MODEL)
    store = SQLiteVectorStore(db_path=SQLITE_PATH)
    
    # Khởi tạo Adapters cho RAG
    ai_client = make_ai()
    userstore = WorkerSessionStore(dynamodb)  # Dùng class mới viết
    vector_store = make_vector()
    
    # FIX BẪY 1: Bẻ lái Vector Store về đúng file chứa 37 chunks
    vector_store.vector_store = store

    original_search = vector_store.search
    def patched_search(query, top_k=5, filter=None, session_id=None):
        # Bỏ qua session_id, chỉ search theo document_id (nếu có)
        return original_search(query, top_k=top_k, filter=filter, session_id=None)
    vector_store.search = patched_search

    queues = [QUEUE_INTERACTIVE_URL, QUEUE_DOCUMENT_URL]
    q_idx = 0

    try:
        while True:
            q_url = queues[q_idx]
            q_idx = (q_idx + 1) % 2
            res = sqs.receive_message(QueueUrl=q_url, MaxNumberOfMessages=1, WaitTimeSeconds=20, VisibilityTimeout=300)
            msgs = res.get("Messages", [])
            if not msgs: continue
            
            msg = msgs[0]
            success = _process_message(msg, q_url, sqs, dynamodb, s3_client, embedder, store, ai_client, userstore, vector_store)
            
            if success:
                sqs.delete_message(QueueUrl=q_url, ReceiptHandle=msg["ReceiptHandle"])
                log_info("message_deleted", queue=q_url.split("/")[-1])
    except KeyboardInterrupt:
        print("\nĐã dừng worker.")

if __name__ == "__main__":
    main()