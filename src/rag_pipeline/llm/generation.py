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
MODEL = os.getenv("OPENAI_MODEL", "gpt-oss-120b")

PROMPT_TEMPLATE = """Bạn là trợ lý AI chuyên về kỹ thuật phần mềm và kiến trúc đám mây. Nhiệm vụ của bạn là trả lời câu hỏi dựa trên các TÀI LIỆU được cung cấp.

TÀI LIỆU (EVIDENCE):
{evidence_text}

QUY TẮC NGHIÊM NGẶT:
1. CHỈ sử dụng thông tin từ TÀI LIỆU được cung cấp. Không sử dụng kiến thức bên ngoài, không tự bịa thông tin.
2. Nếu TÀI LIỆU không chứa đủ thông tin để trả lời, hãy nói rõ: "Tôi không tìm thấy đủ thông tin trong tài liệu."
3. LANGUAGE: Answer in the SAME LANGUAGE as the user's question.
   - English question → English answer
   - Vietnamese question → Vietnamese answer
   - Do NOT default to any specific language.

CRITICAL FORMAT RULES:
- ALWAYS place citations inline immediately after the relevant claim, e.g., "S3 Glacier giá $0.004/GB [sha256:abc123]."
- NEVER use Markdown footnotes [^1], [^2].
- NEVER write a "References", "Chú thích", or footnote definitions section.
- Every factual claim MUST have exactly one [chunk_id] citation at the end.
- EXCEPTION: refusal sentences ("Tôi không tìm thấy...", "I couldn't find...") do NOT need citations.

4. CITATION PRECISION — chỉ cite chunk chứa CHÍNH XÁC thông tin của claim.

   PROCEDURE (thực hiện cho TỪNG claim trước khi viết):
   a) Viết claim.
   b) T tự hỏi: "Chunk nào chứa thông tin TRỰC TIẾP nói về claim này?"
   c) Kiểm tra: đọc lại chunk đó — nó CÓ chứa thông tin không, hay chỉ nói về chủ đề?
   d) Nếu có → cite. Nếu không → BỎ CLAIM hoặc viết lại.

   ĐỊNH NGHĨA "CHỨA THÔNG TIN":
   - Chunk nói: "HNSW giảm O(N) xuống O(log N)"  → support claim "HNSW nhanh hơn"
   - Chunk nói: "HNSW là 1 trong các ANN"        → KHÔNG support claim "HNSW nhanh hơn"

   VÍ DỤ WRONG vs CORRECT (multi-domain):

   [Numeric] WRONG: claim "millions of records" cite chunk không có số
             CORRECT: claim "HNSW dùng cho triệu bản ghi" cite chunk có "triệu bản ghi"

   [Definition] WRONG: claim "tools là thành phần ngoại vi agent gọi"
                     cite chunk về "startup phát triển agent"
              CORRECT: claim "tools là thành phần ngoại vi" cite chunk định nghĩa "tools"

   [Mechanism] WRONG: claim "SQL dùng JOIN và WHERE" cite chunk nói "SQL là database"
              CORRECT: claim "SQL dùng JOIN và WHERE" cite chunk có "JOIN, WHERE"

   HARD RULE: Nếu không có chunk nào chứa thông tin trực tiếp
              → KHÔNG cite bừa. Bỏ claim hoặc trả lời "không đủ thông tin".

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

from src.rag_pipeline.llm.model_rotator import call_with_rotation

def generate_answer(query: str, evidence_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate an answer using OpenAI-compatible API with Model Rotation & Quota Tracking.
    """
    evidence_text, citations = format_evidence(evidence_list)
    prompt = PROMPT_TEMPLATE.format(evidence_text=evidence_text, query=query)
    messages = [
        {"role": "system", "content": "You are a helpful technical assistant. Respond in the SAME LANGUAGE as the user's question (English question → English answer; Vietnamese question → Vietnamese answer). Strictly follow the citation rules."},
        {"role": "user", "content": prompt}
    ]

    try:
        answer, model_used = call_with_rotation(
            client=client,
            messages=messages,
            max_attempts=5,
            threshold=5,
        )
        return {
            "answer": answer,
            "citations": citations,
            "model_used": model_used,
        }
    except Exception as e:
        print(f"Error in generate_answer: {e}")
        return {
            "answer": f"Lỗi khi gọi mô hình: {e}",
            "citations": [],
            "model_used": None,
        }
