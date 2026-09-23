import os
import json
from typing import List, Dict, Any
from openai import OpenAI

# Initialize client using environment variables provided by user
# Note: Using OpenAI SDK since the endpoint is an OpenAI-compatible endpoint (api.mwapi.dev/v1)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "s"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.mwapi.dev/v1")
)
MODEL = os.getenv("OPENAI_MODEL", "claude-sonnet-5")

PROMPT_TEMPLATE = """Bạn là trợ lý AI chuyên về kỹ thuật phần mềm và kiến trúc đám mây. Nhiệm vụ của bạn là trả lời câu hỏi dựa trên các TÀI LIỆU được cung cấp.

TÀI LIỆU (EVIDENCE):
{evidence_text}

QUY TẮC NGHIÊM NGẶT:
1. CHỈ sử dụng thông tin từ TÀI LIỆU được cung cấp. Không sử dụng kiến thức bên ngoài, không tự bịa thông tin.
2. Nếu TÀI LIỆU không chứa đủ thông tin để trả lời, hãy nói rõ: "Tôi không tìm thấy đủ thông tin trong tài liệu."
3. Mọi câu khẳng định (claim) PHẢI kèm theo trích dẫn dạng [1], [2] tương ứng với nguồn tài liệu. 
4. Đặt trích dẫn ngay sau câu hoặc ý được trích xuất từ tài liệu (VD: S3 Glacier có giá $0.004 [1].).
5. Trả lời bằng tiếng Việt, ngắn gọn, súc tích và dễ hiểu.

CÂU HỎI:
{query}
"""

def format_evidence(evidence_list: List[Dict[str, Any]]) -> tuple[str, List[Dict[str, Any]]]:
    """
    Format evidence list into a string for the prompt and build the citations mapping array.
    """
    evidence_text = ""
    citations = []
    
    for i, ev in enumerate(evidence_list, start=1):
        # Build text for the prompt
        evidence_text += f"Tài liệu [{i}]:\n{ev.get('text', '')}\n\n"
        
        # Build citation object mapping to chunk_id
        citations.append({
            "citation_id": str(i),
            "chunk_id": ev.get("chunk_id", ""),
            "document_name": ev.get("document_name", "Unknown"),
            "text": ev.get("text", "")
        })
        
    return evidence_text, citations

def generate_answer(query: str, evidence_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate an answer using the configured OpenAI-compatible API.
    """
    evidence_text, citations = format_evidence(evidence_list)
    
    prompt = PROMPT_TEMPLATE.format(evidence_text=evidence_text, query=query)
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful technical assistant. Always answer in Vietnamese and strictly follow the citation rules."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=1024
        )
        answer = response.choices[0].message.content
        
        return {
            "answer": answer,
            "citations": citations
        }
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return {
            "answer": f"Lỗi khi gọi mô hình: {e}",
            "citations": []
        }
