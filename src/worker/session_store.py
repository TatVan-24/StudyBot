from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from src.worker.config import (
    TABLE_SESSIONS,
    TABLE_SESSION_DOCUMENTS,
    TABLE_DOCUMENTS,
)

class WorkerSessionStore:
    """Adapter đọc Session từ DynamoDB (thay vì SQLite local)."""

    def __init__(self, dynamodb):
        self.sessions_table = dynamodb.Table(TABLE_SESSIONS)
        self.session_docs_table = dynamodb.Table(TABLE_SESSION_DOCUMENTS)
        self.documents_table = dynamodb.Table(TABLE_DOCUMENTS)

    def get_session(self, session_id: str, user_id: str) -> dict:
        # 1. Lấy session từ DynamoDB
        res = self.sessions_table.get_item(Key={"session_id": session_id})
        session = res.get("Item")
        # 2. Kiểm tra quyền sở hữu (bảo mật)
        if session and session.get("user_id") == user_id:
            return session
        return None

    def get_session_docs(self, session_id: str) -> list:
        # Query bảng mapping session-document
        res = self.session_docs_table.query(
            KeyConditionExpression=Key("session_id").eq(session_id)
        )
        # Trả về list các document_id
        return [item["document_id"] for item in res.get("Items", [])]

    def next_turn_index(self, session_id: str) -> int:
        # MVP: Trả về 1 (hoặc bạn có thể query Messages để đếm nếu muốn)
        return 1

    def log_query(self, *args, **kwargs):
        # RAG pipeline gọi hàm này, nhưng Worker tự lưu message ở bước sau, nên bỏ qua
        pass

    def update_session_activity(self, session_id: str):
        # Cập nhật thời gian hoạt động cuối cùng
        now_iso = datetime.now(timezone.utc).isoformat()
        self.sessions_table.update_item(
            Key={"session_id": session_id},
            UpdateExpression="SET updated_at = :u",
            ExpressionAttributeValues={":u": now_iso}
        )

    def get_active_session_docs(self, session_id: str) -> list:
        document_ids = self.get_session_docs(session_id)

        active_document_ids = []

        for document_id in document_ids:
            res = self.documents_table.get_item(
                Key={"document_id": document_id}
            )
            document = res.get("Item")

            if document and document.get("status") == "ACTIVE":
                active_document_ids.append(document_id)

        return active_document_ids