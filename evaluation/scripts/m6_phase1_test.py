import time
import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
TEST_FILE_PATH = "evaluation/raw_pdf/test_notes.txt"

def create_dummy_txt():
    Path("evaluation/raw_pdf").mkdir(parents=True, exist_ok=True)
    content = """# Machine Learning Basics
Machine learning is a subfield of artificial intelligence.
It involves algorithms that learn from data.

## Types of ML
1. Supervised Learning: Uses labeled data.
2. Unsupervised Learning: Uses unlabeled data.
3. Reinforcement Learning: Learns via reward and punishment.
"""
    with open(TEST_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    return TEST_FILE_PATH

def benchmark_upload(file_path):
    print(f"\n--- Testing POST /upload ---")
    start = time.time()
    with open(file_path, "rb") as f:
        files = {"file": (Path(file_path).name, f, "text/plain")}
        headers = {"x-user-id": "local-test-user"}
        resp = requests.post(f"{BASE_URL}/upload", files=files, headers=headers)
    latency = time.time() - start
    print(f"Status: {resp.status_code}")
    print(f"Latency: {latency:.4f} seconds")
    try:
        print(f"Response: {resp.json()}")
    except:
        print(f"Raw response: {resp.text}")
    assert resp.status_code == 200, "Upload failed!"

def benchmark_query(question, label="First-request"):
    print(f"\n--- Testing POST /query ({label}) ---")
    start = time.time()
    payload = {"question": question}
    headers = {"x-user-id": "local-test-user"}
    resp = requests.post(f"{BASE_URL}/query", json=payload, headers=headers)
    latency = time.time() - start
    print(f"Status: {resp.status_code}")
    print(f"Latency: {latency:.4f} seconds")
    try:
        print(f"Response: {resp.json()}")
    except:
        print(f"Raw response: {resp.text}")
    assert resp.status_code == 200, "Query failed!"

if __name__ == "__main__":
    print("Checking if server is up...")
    try:
        health = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {health.json()}")
    except Exception as e:
        print("Server is not running. Start it with: uvicorn src.backend.app:app --reload")
        exit(1)

    txt_path = create_dummy_txt()
    
    # 1. Upload Test
    benchmark_upload(txt_path)
    
    # 2. First-request latency (Cold query)
    benchmark_query("What is supervised learning?", label="First-request")
    
    # 3. Warm-request latency
    benchmark_query("Tell me about reinforcement learning.", label="Warm-request")
    
    print("\n[✔] Phase 1 Integration Smoke Test Completed.")
