import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    base_url=os.getenv('OPENAI_BASE_URL')
)

prompt = """Bạn là trợ lý AI chuyên về kỹ thuật phần mềm và kiến trúc đám mây. Nhiệm vụ của bạn là trả lời câu hỏi dựa trên các TÀI LIỆU được cung cấp.

TÀI LIỆU (EVIDENCE):
Tài liệu [abc-123]:
Vector Database (Cơ sở dữ liệu Vector) là một loại cơ sở dữ liệu chuyên biệt được thiết kế để lưu trữ, quản lý và truy xuất các vector embeddings (các mảng số biểu diễn dữ liệu) một cách hiệu quả.

QUY TẮC NGHIÊM NGẶT:
1. CHỈ sử dụng thông tin từ TÀI LIỆU được cung cấp.
2. Mọi câu khẳng định PHẢI kèm theo trích dẫn dạng [chunk_id].
3. Ví dụ: Vector Database lưu trữ vector [abc-123].

CÂU HỎI:
Vector database là gì?
"""

print("Sending request to Gemini...")
response = client.chat.completions.create(
    model=os.getenv('OPENAI_MODEL'),
    messages=[
        {"role": "system", "content": "You are a helpful technical assistant."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.0,
    max_tokens=1024
)

choice = response.choices[0]
answer = choice.message.content
finish_reason = choice.finish_reason

print("\n=== RAW ANSWER ===")
print(answer)
print("==================")
print(f"Finish Reason: {finish_reason}")

import re
citations = re.findall(r"\[(.*?)\]", answer if answer else "")
print(f"Extracted Citations: {citations}")
