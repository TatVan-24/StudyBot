import json
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://127.0.0.1:8000"
CASES_PATH = Path(__file__).parent / "test_cases.jsonl"
REPORT_PATH = Path(__file__).parent / "test_report.json"

UI_STATUS_MAP = {
    "grounded": "GROUNDED",
    "ambiguous": "AMBIGUOUS",
    "rejection": "REJECT",
}

def load_cases():
    with open(CASES_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def login(driver):
    driver.get(BASE_URL)
    # Bypass màn hình Auth (Login Modal) bằng JS và đăng nhập với tư cách user mixigaming@gmail.com
    driver.execute_script("saveSession({name: 'Mixi Gaming', email: 'mixigaming@gmail.com'}, false)")

    # Wait cho #question thực sự VISIBLE (không bị hide bởi auth-view)
    WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.ID, "question"))
    )

def ask_query(driver, query):
    textarea = driver.find_element(By.ID, "question")

    # Đảm bảo cuộn tới element trước khi tương tác
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", textarea)
    time.sleep(0.5)

    textarea.clear()
    textarea.send_keys(query)

    # Cuộn tới nút Ask và click
    ask_btn = driver.find_element(By.ID, "ask-btn")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", ask_btn)
    ask_btn.click()

    # Đợi bot message xuất hiện (không còn spinner)
    WebDriverWait(driver, 60).until(
        lambda d: not d.find_elements(By.CSS_SELECTOR, ".chat-message.bot .spinner")
        and len(d.find_elements(By.CSS_SELECTOR, ".chat-message.bot")) > 0
    )

    # Lấy message bot cuối cùng
    bot_messages = driver.find_elements(By.CSS_SELECTOR, ".chat-message.bot")
    last = bot_messages[-1]

    # Lấy status badge
    badge = last.find_elements(By.CSS_SELECTOR, ".status-badge")
    status = "unknown"
    if badge:
        badge_text = badge[0].text.lower()
        for key, val in UI_STATUS_MAP.items():
            if key in badge_text:
                status = val
                break

    # Lấy answer text
    answer_el = last.find_elements(By.CSS_SELECTOR, ".answer-text")
    answer = answer_el[0].text if answer_el else ""

    # Đếm số lượng citations
    citations = last.find_elements(By.CSS_SELECTOR, ".citation")

    return {
        "status": status,
        "answer": answer,
        "citation_count": len(citations),
    }

def run_tests():
    cases = load_cases()
    print(f"Khởi động Selenium để chạy {len(cases)} test cases...")

    try:
        driver = setup_driver()
    except Exception as e:
        print(f"Lỗi: Không thể khởi động Chrome WebDriver. Đảm bảo Chrome được cài đặt.\nChi tiết: {e}")
        return

    try:
        login(driver)
        print("Đã tải giao diện thành công, bắt đầu test...")

        results = []
        for i, case in enumerate(cases, 1):
            print(f"[{i:02d}/{len(cases)}] {case['id']}: {case['query'][:50]}...", end=" ", flush=True)

            try:
                actual = ask_query(driver, case["query"])
                passed = actual["status"] == case["expected_class"]

                print(f"-> {actual['status']} ({'PASS' if passed else 'FAIL'})")

                results.append({
                    "id": case["id"],
                    "query": case["query"],
                    "expected": case["expected_class"],
                    "actual": actual["status"],
                    "pass": passed,
                    "answer_preview": actual["answer"][:100].replace('\n', ' '),
                    "citation_count": actual["citation_count"],
                })
            except Exception as e:
                print(f"-> ERROR")
                results.append({
                    "id": case["id"],
                    "query": case["query"],
                    "expected": case["expected_class"],
                    "actual": "ERROR",
                    "pass": False,
                    "error": str(e),
                })
            time.sleep(1) # Nghỉ chút để UI ổn định

        # Save report
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # Summary
        passed = sum(1 for r in results if r["pass"])
        print(f"\n=== Kết quả Test (Selenium UI) ===")
        print(f"Tổng cộng: {len(results)} | PASS: {passed} | FAIL: {len(results) - passed}")
        print(f"Độ chính xác (Accuracy): {passed/len(results)*100:.1f}%")
        print(f"Report JSON lưu tại: {REPORT_PATH}")
        print(f"Logs AIOps chi tiết lưu tại thư mục: _data/logs/")

    finally:
        driver.quit()

if __name__ == "__main__":
    run_tests()
