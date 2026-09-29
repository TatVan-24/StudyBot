import requests
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
USER_ID = "mixigaming@gmail.com"

print("1. Tạo session mới bằng cách upload 1 file...")
doc_path = None
# Tìm tạm 1 file PDF bất kỳ trong thư mục upload để test
for p in Path("_data/uploads/mixigaming@gmail.com").rglob("*.pdf"):
    doc_path = p
    break

if not doc_path:
    print("Không tìm thấy file PDF nào để upload. Bạn hãy tạo một file dummy.txt để test.")
    exit(1)

with open(doc_path, "rb") as f:
    resp = requests.post(
        f"{BASE_URL}/upload",
        files={"file": (doc_path.name, f, "application/pdf")},
        headers={"X-User-Id": USER_ID},
    )

session_id = resp.json().get("session_id")
print(f"-> Đã tạo Session mới: {session_id}")

print("\n2. Query 'vector database' ngay trên Session vừa tạo...")
query_payload = {
    "session_id": session_id,
    "user_id": USER_ID,
    "query": "vector database",
}

resp_query = requests.post(
    f"{BASE_URL}/query",
    json=query_payload,
)

print(f"-> HTTP Status: {resp_query.status_code}")
try:
    data = resp_query.json()
    print("-> Response Data:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print("-> Lỗi parse JSON:", e)
    print("Raw text:", resp_query.text)
