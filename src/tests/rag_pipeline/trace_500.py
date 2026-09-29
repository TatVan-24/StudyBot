import sys
import traceback
from pathlib import Path
from fastapi.testclient import TestClient
from src.backend.app import app

client = TestClient(app)

print("1. Upload file để tạo session...")
USER_ID = "mixigaming@gmail.com"
doc_path = None
# Tìm tạm 1 file PDF bất kỳ trong thư mục upload để test
for p in Path("_data/uploads/mixigaming@gmail.com").rglob("*.pdf"):
    doc_path = p
    break

if not doc_path:
    print("Không tìm thấy file PDF nào để upload. Bạn hãy tạo một file dummy.pdf để test.")
    sys.exit(1)

with open(doc_path, "rb") as f:
    resp_up = client.post(
        "/upload",
        files={"file": (doc_path.name, f, "application/pdf")},
        headers={"X-User-Id": USER_ID}
    )

if resp_up.status_code != 200:
    print(f"Upload failed: {resp_up.status_code} - {resp_up.text}")
    sys.exit(1)

session_id = resp_up.json().get("session_id")
print(f"-> Đã tạo Session mới (có document): {session_id}")

print("\n2. Sending query to trigger 500 error...")
try:
    resp = client.post("/query", json={
        "session_id": session_id,
        "user_id": USER_ID,
        "query": "vector database"
    })
    print(f"HTTP Status: {resp.status_code}")
    print("Response text:", resp.text)
except Exception as e:
    print("\n--- TRACEBACK 500 START ---")
    traceback.print_exc()
    print("--- TRACEBACK 500 END ---")
