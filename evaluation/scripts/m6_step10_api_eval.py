import time
import requests
import json
import os

API_URL = "http://127.0.0.1:8000"
USER_ID = "demo@studybot.local"
REPORT_PATH = os.path.join(os.path.dirname(__file__), "..", "reports", "m6_generation_report.md")

test_cases = [
    {
        "type": "Answerable Case",
        "query": "vector database là gì?"
    },
    {
        "type": "Unanswerable Case",
        "query": "giải thích chi tiết thuật toán băm (hashing) trong blockchain"
    },
    {
        "type": "Cross-document Case",
        "query": "so sánh vector database và quá trình chunking"
    }
]

def run_eval():
    print(f"Bắt đầu chạy API Evaluation cho M6 Generation...")
    
    # 1. Đảm bảo API Backend đang chạy
    try:
        requests.get(f"{API_URL}/health", timeout=3)
    except Exception as e:
        print(f"Lỗi: Không thể kết nối tới Backend tại {API_URL}. Vui lòng đảm bảo uvicorn đang chạy.")
        return

    results = []
    
    # 2. Chạy test cases
    for case in test_cases:
        print(f"\n[Testing {case['type']}] Query: {case['query']}")
        start_t = time.time()
        
        headers = {"x-user-id": USER_ID}
        payload = {"question": case["query"]}
        
        resp = requests.post(f"{API_URL}/query", json=payload, headers=headers)
        latency = time.time() - start_t
        
        if resp.status_code == 200:
            data = resp.json()
            status = data.get("status")
            meta = data.get("data", {}).get("metadata", {})
            citations = data.get("data", {}).get("citations", [])
            answer = data.get("data", {}).get("answer", "")
            
            print(f"  -> Status: {status.upper()} | Latency: {latency:.2f}s")
            
            results.append({
                "case": case["type"],
                "query": case["query"],
                "status": status,
                "answer": answer,
                "citations_count": len(citations),
                "latency_sec": latency,
                "reason": meta.get("reason", "N/A")
            })
        else:
            print(f"  -> Lỗi API: {resp.status_code} - {resp.text}")
            results.append({
                "case": case["type"],
                "query": case["query"],
                "status": "API_ERROR",
                "latency_sec": latency
            })
            
    # 3. Tạo Report Markdown
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# M6 Generation & Refusal API Evaluation Report\n\n")
        f.write("Báo cáo đánh giá tích hợp Generation (M6) với LLM OpenAI Claude-3.5 qua API nội bộ.\n\n")
        
        f.write("## 1. Tóm tắt chỉ số (Metrics)\n\n")
        avg_latency = sum(r["latency_sec"] for r in results) / len(results) if results else 0
        f.write(f"- **Tốc độ xử lý trung bình (API Latency):** {avg_latency:.2f}s/query\n")
        
        refusals = [r for r in results if r["status"] == "rejection"]
        f.write(f"- **Tỷ lệ Refusal:** {len(refusals)}/{len(results)} ({len(refusals)/len(results)*100 if results else 0:.0f}%)\n")
        f.write("- **System Identity:** Claude-3.5-Sonnet (thông qua mwapi), sử dụng `OpenAIAdapter`.\n\n")
        
        f.write("## 2. Chi tiết Test Cases\n\n")
        for r in results:
            f.write(f"### {r['case']}\n")
            f.write(f"- **Query:** `{r['query']}`\n")
            f.write(f"- **Status:** `{r['status']}`\n")
            f.write(f"- **Latency:** {r.get('latency_sec', 0):.2f}s\n")
            
            if r["status"] == "rejection":
                f.write(f"- **Lý do từ chối (Reason):** {r.get('reason')}\n")
            else:
                f.write(f"- **Số lượng Citation:** {r.get('citations_count')}\n")
            
            f.write(f"- **Answer:**\n> {r.get('answer', '').replace(chr(10), chr(10)+'> ')}\n\n")
            
    print(f"\n[Hoàn tất] Báo cáo đã được ghi ra: {REPORT_PATH}")

if __name__ == "__main__":
    run_eval()
