"""AI adapters. Pick via AI_BACKEND env var.

Interface:
    invoke(prompt, **kwargs) -> str
    retrieve_and_generate(query, kb_id="") -> dict with {"answer": str, "citations": list}
"""
from typing import Any


class BedrockAI:
    """Real Amazon Bedrock client. Uses Converse API for invoke; bedrock-agent-runtime for RAG."""

    def __init__(self, region: str, model_id: str):
        import boto3
        self.region = region
        self.model_id = model_id
        self.runtime = boto3.client("bedrock-runtime", region_name=region)
        self.agent_runtime = boto3.client("bedrock-agent-runtime", region_name=region)

    def invoke(self, prompt: str, **kwargs: Any) -> str:
        max_tokens = kwargs.get("max_tokens", 1024)
        resp = self.runtime.converse(
            modelId=self.model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": kwargs.get("temperature", 0.2)},
        )
        return resp["output"]["message"]["content"][0]["text"]

    def retrieve_and_generate(self, query: str, kb_id: str = "") -> dict:
        if not kb_id:
            raise ValueError("VECTOR_BEDROCK_KB_ID must be set for Bedrock KB retrieve_and_generate")
        model_arn = f"arn:aws:bedrock:{self.region}::foundation-model/{self.model_id}"
        resp = self.agent_runtime.retrieve_and_generate(
            input={"text": query},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": kb_id,
                    "modelArn": model_arn,
                },
            },
        )
        return {
            "answer": resp["output"]["text"],
            "citations": [
                {
                    "text": ref.get("content", {}).get("text", ""),
                    "source": ref.get("location", {}),
                }
                for citation in resp.get("citations", [])
                for ref in citation.get("retrievedReferences", [])
            ],
        }


class LocalAI:
    """Local stub. Returns canned responses. Use for development without AWS credentials."""

    def invoke(self, prompt: str, **kwargs: Any) -> str:
        snippet = prompt[:200].replace("\n", " ")
        return (
            f"[LOCAL_AI_STUB] Received prompt: {snippet!r}... "
            "Set AI_BACKEND=bedrock + AWS credentials for real Bedrock output."
        )

    def retrieve_and_generate(self, query: str, kb_id: str = "") -> dict:
        return {
            "answer": (
                f"[LOCAL_AI_STUB] Query received: {query!r}. "
                "Set AI_BACKEND=bedrock and VECTOR_BACKEND=bedrock_kb for real RAG."
            ),
            "citations": [],
        }


class OpenAIAdapter:
    """Uses OpenAI SDK for API endpoints (like Claude via mwapi)."""

    def __init__(self, api_key: str, base_url: str, model: str):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def generate_with_citations(self, query: str, chunks: list) -> dict:
        import re

        # Build prompt with [chunk_id] inline
        evidence_text = ""
        for c in chunks:
            chunk_id = c.get("doc_id", "unknown")
            text = c.get("text", "")
            evidence_text += f"Tài liệu [{chunk_id}]:\n{text}\n\n"

        prompt = f"""Bạn là trợ lý AI chuyên về kỹ thuật phần mềm và kiến trúc đám mây. Nhiệm vụ của bạn là trả lời câu hỏi dựa trên các TÀI LIỆU được cung cấp.

TÀI LIỆU (EVIDENCE):
{evidence_text}

QUY TẮC NGHIÊM NGẶT:
1. CHỈ sử dụng thông tin từ TÀI LIỆU được cung cấp. Không sử dụng kiến thức bên ngoài, không tự bịa thông tin.
2. Nếu TÀI LIỆU không chứa đủ thông tin để trả lời, hãy nói rõ: "Tôi không tìm thấy đủ thông tin trong tài liệu."
3. Mọi câu khẳng định (claim) PHẢI kèm theo trích dẫn dạng [chunk_id] tương ứng với nguồn tài liệu.
4. Đặt trích dẫn ngay sau câu hoặc ý được trích xuất từ tài liệu (VD: S3 Glacier có giá $0.004 [sha256:123abc...].).
5. Chỉ trích dẫn các tài liệu thực sự hỗ trợ cho câu khẳng định đó.
6. Trả lời bằng tiếng Việt, ngắn gọn, súc tích và dễ hiểu.

CÂU HỎI:
{query}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful technical assistant. Always answer in Vietnamese and strictly follow the citation rules."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=1024
            )
            answer = response.choices[0].message.content
        except Exception as e:
            print(f"Error calling LLM: {e}")
            answer = f"Lỗi khi gọi mô hình: {e}"

        # Parse citations from answer using regex: looking for [chunk_id]
        # We find all [something] and see if it's in our chunks
        cited_ids = []
        matches = re.findall(r"\[(.*?)\]", answer)
        for match in matches:
            cited_ids.append(match)

        # Build citation list (matching the expected format)
        citations = []
        unique_cited = set(cited_ids)
        for c in chunks:
            cid = c.get("doc_id", "")
            if cid in unique_cited:
                citations.append({
                    "citation_id": cid,
                    "chunk_id": cid,
                    "document_name": c.get("metadata", {}).get("filename", "Unknown"),
                    "text": c.get("text", "")
                })

        return {
            "answer": answer,
            "citations": citations
        }
