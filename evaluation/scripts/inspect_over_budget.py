import json

chunks = []
with open('evaluation/runs/m2-final/chunks_structure.jsonl', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            chunks.append(json.loads(line))

over = [c for c in chunks if c['token_count'] > 256]
max_tok = max((c['token_count'] for c in over), default=0)
print(f'Over-budget: {len(over)}, max_tokens={max_tok}')
for c in over:
    print(f'  idx={c["chunk_index"]} doc={c["document_id"]} tok={c["token_count"]} | {repr(c["text"][:100])}')
