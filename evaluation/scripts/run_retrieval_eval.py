import json
import sys
import os
import datetime
from pathlib import Path
from typing import List, Dict, Any, Set

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.indexer.embedding import EmbeddingEngine
from src.indexer.vector_store import SQLiteVectorStore
from evaluation.scripts.validate_resolution import load_blocks, match_locator

DEV_V2_PATH = "d:/Personal Project/AWS StudyBot/evaluation/datasets/development-v2.jsonl"
INDEX_PATH = "d:/Personal Project/AWS StudyBot/evaluation/index/m3_index.db"
OUTPUT_PATH = "d:/Personal Project/AWS StudyBot/evaluation/results/m4_eval_results.jsonl"

K_VALUES = [1, 3, 5, 10]
MAX_K = max(K_VALUES)

def resolve_ground_truth(case: Dict[str, Any], blocks_by_doc: Dict[str, List[Dict]]) -> Set[str]:
    target_block_ids = set()
    for ev in case.get('evidence', []):
        doc_id = ev.get('document_id')
        gt_locator = ev.get('locator')
        
        doc_blocks = blocks_by_doc.get(doc_id, [])
        for b in doc_blocks:
            if match_locator(gt_locator, b):
                target_block_ids.add(b['block_id'])
    return target_block_ids

def run_retrieval(query_text: str, engine: EmbeddingEngine, store: SQLiteVectorStore, top_k: int) -> List[Any]:
    q_vector = engine.encode([query_text])[0]
    return store.search(q_vector, top_k=top_k)

def verify_embedding_invariant(engine: EmbeddingEngine, store: SQLiteVectorStore):
    """System-level invariant: query engine and index MUST use same model/dimension/normalization.
    Fail-Fast if mismatch detected to prevent silently computing wrong scores.
    """
    index_meta = store.load_meta()
    if index_meta is None:
        print("[FAIL FAST] Index metadata missing. Cannot verify embedding invariant.")
        sys.exit(1)

    mismatches = []
    if index_meta.model_name != engine.model_name:
        mismatches.append(f"  model_name:    index={index_meta.model_name!r} vs engine={engine.model_name!r}")
    if index_meta.dimension != engine.dimension:
        mismatches.append(f"  dimension:     index={index_meta.dimension} vs engine={engine.dimension}")
    if index_meta.normalization != engine.normalization:
        mismatches.append(f"  normalization: index={index_meta.normalization!r} vs engine={engine.normalization!r}")

    if mismatches:
        print("[FAIL FAST] Embedding invariant violated! Query engine != Index model:")
        for m in mismatches:
            print(m)
        print("Fix: Initialize EmbeddingEngine with the same model used to build the index.")
        sys.exit(1)

    print(f"[OK] Embedding invariant verified: model={index_meta.model_name!r}, dim={index_meta.dimension}, norm={index_meta.normalization!r}")
    return index_meta

def check_blocks_in_index(target_block_ids: Set[str], store: SQLiteVectorStore) -> bool:
    """Verify that ALL target blocks have at least one chunk in the index.
    Uses exact JSON parse, no LIKE substring matching (D1 contract).
    """
    import sqlite3
    with sqlite3.connect(store.db_path) as conn:
        cursor = conn.execute("SELECT source_block_ids FROM embeddings")
        indexed_block_ids: Set[str] = set()
        for (raw,) in cursor.fetchall():
            for bid in json.loads(raw):
                indexed_block_ids.add(bid)
    return target_block_ids.issubset(indexed_block_ids)

def evaluate(case_id: str, target_block_ids: Set[str], retrieved_chunks: List[Any], store: SQLiteVectorStore):
    coverage_at_k = {}
    cumulative_blocks = set()
    
    first_hit_rank = -1
    full_coverage_rank = -1
    
    top_k_trace = []
    total_target = len(target_block_ids)
    
    for rank, chunk in enumerate(retrieved_chunks, 1):
        chunk_block_ids = set(chunk.source_block_ids)
        provided_evidence = target_block_ids.intersection(chunk_block_ids)
        
        cumulative_blocks.update(provided_evidence)
        current_coverage = len(cumulative_blocks) / total_target if total_target > 0 else 0.0
        
        if len(provided_evidence) > 0 and first_hit_rank == -1:
            first_hit_rank = rank
            
        if current_coverage == 1.0 and full_coverage_rank == -1:
            full_coverage_rank = rank
            
        coverage_at_k[rank] = current_coverage
        
        top_k_trace.append({
            "rank": rank,
            "chunk_id": chunk.chunk_id,
            "score": round(float(chunk.score), 4),
            "source_block_ids": list(chunk.source_block_ids),
            "provided_evidence": list(provided_evidence)
        })
        
    for k in K_VALUES:
        if k not in coverage_at_k:
            prev_rank = max([r for r in coverage_at_k.keys() if r < k], default=0)
            coverage_at_k[k] = coverage_at_k.get(prev_rank, 0.0)
            
    mrr_first_hit = 1.0 / first_hit_rank if first_hit_rank > 0 else 0.0
    mrr_full_coverage = 1.0 / full_coverage_rank if full_coverage_rank > 0 else 0.0
    
    blocks_exist = check_blocks_in_index(target_block_ids, store)
    blocks_retrieved = len(cumulative_blocks) > 0
    uncovered = list(target_block_ids - cumulative_blocks)
    
    return {
        "metrics": {
            f"coverage_at_{k}": coverage_at_k[k] for k in K_VALUES
        } | {
            "mrr_first_hit": mrr_first_hit,
            "mrr_full_coverage": mrr_full_coverage
        },
        "top_k_chunks": top_k_trace,
        "diagnostic_evidence": {
            "target_blocks_exist_in_index": blocks_exist,
            "target_blocks_retrieved": blocks_retrieved,
            "first_hit_rank": first_hit_rank,
            "full_coverage_rank": full_coverage_rank,
            "uncovered_block_ids": uncovered
        }
    }

def generate_summary(path: str, artifacts: list, retrieval_config: dict, run_metadata: dict, num_cases: int, metrics_sums: dict):
    n = num_cases
    mean = lambda k: metrics_sums[k] / n

    lines = []
    w = lines.append

    w("# M4 — Retrieval Evaluation Summary\n")

    # ── Section 1: Overview ──────────────────────────────────────────────────
    w("## 1. Evaluation Overview\n")
    w("| Item | Value |")
    w("|---|---|")
    w(f"| Dataset | {run_metadata['dataset']} |")
    w(f"| Evaluation cases | {n} |")
    w(f"| Retrieval scope | Global Search |")
    w(f"| Embedding model | {retrieval_config['embedding_model']} |")
    w(f"| Embedding dimension | {retrieval_config['embedding_dimension']} |")
    w(f"| Normalization | {retrieval_config['normalization']} |")
    w(f"| Similarity metric | {retrieval_config['metric']} |")
    w(f"| Retrieval K | {', '.join(str(k) for k in K_VALUES)} |")
    w(f"| Index version | {retrieval_config.get('index_version', 'unknown')} |")
    w(f"| Run timestamp | {run_metadata['timestamp']} |")
    w(f"| Ground-truth unit | ParsedBlock |")
    w(f"| Relevance definition | chunk.source_block_ids ∩ target_block_ids |")
    w(f"| Evaluation status | COMPLETED |")
    w("")

    # ── Section 2: Aggregate Metrics ─────────────────────────────────────────
    w("---\n")
    w("## 2. Metric Results\n")
    w("| Metric | Mean |")
    w("|---|---:|")
    for k in K_VALUES:
        w(f"| Coverage@{k} | {mean(f'coverage_at_{k}') * 100:.2f}% |")
    w(f"| MRR — First Hit | {mean('mrr_first_hit'):.4f} |")
    w(f"| MRR — Full Coverage | {mean('mrr_full_coverage'):.4f} |")
    w("")
    w("### Interpretation\n")
    w(f"The retriever finds at least one relevant block at a relatively high rank "
      f"(MRR First Hit = **{mean('mrr_first_hit'):.4f}**).\n")
    w(f"However cumulative evidence coverage remains limited:\n")
    for k in K_VALUES:
        w(f"- At Top-{k}, mean coverage is **{mean(f'coverage_at_{k}') * 100:.2f}%**.")
    w(f"\nMRR Full Coverage = **{mean('mrr_full_coverage'):.4f}** — full evidence retrieval is rarely achieved.")
    w("")

    # ── Section 3: Per-Case Table ─────────────────────────────────────────────
    w("---\n")
    w("## 3. Per-Case Results\n")
    header = "| Case | Target Blocks |" + "".join(f" Cov@{k} |" for k in K_VALUES) + " First Hit | Full Cov |"
    sep    = "|---|---:|" + "---:|" * len(K_VALUES) + "---:|---:|"
    w(header)
    w(sep)
    for a in artifacts:
        m = a['metrics']
        diag = a['diagnostic_evidence']
        first_hit = f"#{diag['first_hit_rank']}" if diag['first_hit_rank'] > 0 else "—"
        full_cov  = "Yes" if diag['full_coverage_rank'] > 0 else "No"
        cov_cols  = "".join(f" {m[f'coverage_at_{k}'] * 100:.1f}% |" for k in K_VALUES)
        w(f"| {a['case_id']} | {a['total_target_blocks']} |{cov_cols} {first_hit} | {full_cov} |")
    w("")

    # ── Section 4: Case-Level Observations ───────────────────────────────────
    w("---\n")
    w("## 4. Case-Level Observations\n")

    perfect = [a for a in artifacts if a['metrics'][f'coverage_at_{MAX_K}'] == 1.0]
    zero    = [a for a in artifacts if a['metrics'][f'coverage_at_{MAX_K}'] == 0.0]
    partial = [a for a in artifacts if 0.0 < a['metrics'][f'coverage_at_{MAX_K}'] < 1.0]
    late    = [a for a in artifacts if a['diagnostic_evidence']['first_hit_rank'] > 3
                                    and a['diagnostic_evidence']['first_hit_rank'] > 0]

    if perfect:
        w("### 4.1 Full Coverage Cases\n")
        for a in perfect:
            diag = a['diagnostic_evidence']
            w(f"#### `{a['case_id']}`\n")
            w(f"- Target blocks: {a['total_target_blocks']}")
            w(f"- Coverage@{MAX_K}: 100%")
            w(f"- First relevant result: Rank #{diag['first_hit_rank']}")
            w(f"- Full coverage achieved at Rank #{diag['full_coverage_rank']}")
            w("")

    if partial:
        w("### 4.2 Partial Retrieval Cases\n")
        for a in partial:
            diag = a['diagnostic_evidence']
            m = a['metrics']
            w(f"#### `{a['case_id']}`\n")
            for k in K_VALUES:
                w(f"- Coverage@{k}: {m[f'coverage_at_{k}'] * 100:.1f}%")
            w(f"- Uncovered blocks: {diag['uncovered_block_ids'][:5]}{'...' if len(diag['uncovered_block_ids']) > 5 else ''}")
            w("")

    if late:
        w("### 4.3 Late Retrieval Cases\n")
        for a in late:
            diag = a['diagnostic_evidence']
            m = a['metrics']
            w(f"#### `{a['case_id']}`\n")
            w(f"- First relevant chunk appears at Rank #{diag['first_hit_rank']}.")
            w(f"- Coverage@1 = {m['coverage_at_1'] * 100:.1f}%  →  Coverage@{MAX_K} = {m[f'coverage_at_{MAX_K}'] * 100:.1f}%")
            w("")

    if zero:
        w("### 4.4 Clean Misses (Coverage@K = 0)\n")
        for a in zero:
            diag = a['diagnostic_evidence']
            w(f"#### `{a['case_id']}`\n")
            w(f"```")
            w(f"Target blocks exist in index : {diag['target_blocks_exist_in_index']}")
            w(f"Retrieved in Top-{MAX_K}       : {diag['target_blocks_retrieved']}")
            w(f"Coverage@{MAX_K}               : 0%")
            w(f"```")
            if diag['target_blocks_exist_in_index']:
                w("The target blocks exist in the index but were not retrieved. "
                  "This is a retrieval failure, not a corpus-absence failure.")
            else:
                w("The target blocks do not exist in the index. "
                  "This may indicate a parsing or ingestion failure.")
            w("")

    # ── Section 5: Findings ───────────────────────────────────────────────────
    w("---\n")
    w("## 5. Important Findings\n")
    w("### Finding 1 — Retrieval pipeline is functional\n")
    w(f"All {n} evaluation cases were executed successfully. "
      "Embedding invariant verified. Target blocks resolved. Traces generated.\n")

    gap = mean('mrr_first_hit') - mean('mrr_full_coverage')
    w("### Finding 2 — First-hit retrieval is substantially better than full coverage\n")
    w(f"```")
    w(f"MRR First Hit      = {mean('mrr_first_hit'):.4f}")
    w(f"MRR Full Coverage  = {mean('mrr_full_coverage'):.4f}")
    w(f"Gap                = {gap:.4f}")
    w(f"```")
    w("The retriever can often surface some relevant evidence, "
      "but retrieving the **complete evidence set** is much harder.\n")

    if zero:
        w("### Finding 3 — Target evidence exists for the failed cases\n")
        exist_and_missed = [a for a in zero if a['diagnostic_evidence']['target_blocks_exist_in_index']]
        if exist_and_missed:
            w("The following zero-hit cases have target blocks present in the index:\n")
            for a in exist_and_missed:
                w(f"- `{a['case_id']}`")
            w("\nTherefore these are **retrieval failures**, not corpus gaps.\n")

    w("### Finding 4 — Global Search causes cross-document competition\n")
    w("Non-target document chunks compete directly with relevant evidence. "
      "This is expected behavior under D5 (Global Search) and should be treated "
      "as evaluation evidence, not as an implementation bug.\n")

    # ── Section 6: Limitations ────────────────────────────────────────────────
    w("---\n")
    w("## 6. Current Limitations\n")
    w("The current M4 results do **not** yet establish:\n")
    for limitation in [
        "that the embedding model is inadequate",
        "that the chunker is the root cause",
        "that the queries are poorly written",
        "that Global Search should be replaced by scoped search",
        "that a reranker is required",
    ]:
        w(f"- {limitation}")
    w("\nThe current trace provides **failure evidence**, but not sufficient evidence "
      "to assign a definitive root cause.\n")

    # ── Section 7: Verdict ────────────────────────────────────────────────────
    w("---\n")
    w("## 7. M4 Baseline Verdict\n")
    w("### Pipeline Integrity\n")
    w("**PASS**\n")
    w(f"- {n}/{n} cases executed")
    w("- Embedding invariant verified")
    w("- Target blocks resolved")
    w("- Target blocks checked against index")
    w("- Retrieval traces generated\n")
    w("### Retrieval Quality\n")
    w("**BASELINE ESTABLISHED — QUALITY REQUIRES INVESTIGATION**\n")
    w("> The retriever can consistently find relevant evidence in some cases, "
      "but evidence coverage is incomplete and several queries produce substantial retrieval misses.\n")

    # ── Section 8: Next Investigation ────────────────────────────────────────
    w("---\n")
    w("## 8. Next Investigation\n")
    w("Before changing the retriever, inspect the failure cases at the evidence level:\n")
    for item in ["Ground-truth block text", "Retrieved chunk text", "Query text",
                 "Chunk boundaries", "Target/non-target semantic similarity",
                 "Ranking position", "Cross-document distractors"]:
        w(f"1. {item}" if item == "Ground-truth block text" else f"- {item}")
    w("")
    if zero:
        w("**Priority cases:**\n")
        w("```")
        for a in zero:
            w(f"P0  {a['case_id']}")
        for a in late:
            w(f"P1  {a['case_id']}")
        w("```")
    w("\nOnly after this inspection should a root-cause category be assigned.")

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def main():
    if not os.path.exists(DEV_V2_PATH):
        print(f"Error: {DEV_V2_PATH} does not exist.")
        sys.exit(1)
        
    print("Loading Mapping Data (Blocks)...")
    blocks_by_doc = load_blocks()
    print("Initializing Embedding Engine...")
    engine = EmbeddingEngine()
    print("Connecting to Vector Store...")
    store = SQLiteVectorStore(INDEX_PATH)
    
    cases = []
    with open(DEV_V2_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            cases.append(json.loads(line))
            
    print(f"\nStarting Evaluation for {len(cases)} cases...")

    # --- LAST GATE: Verify query engine == index model (Fail-Fast) ---
    index_meta = verify_embedding_invariant(engine, store)

    run_metadata = {
        "run_id": "m4-baseline-v1",
        "dataset": "development-v2",
        "index": "m3_index.db",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }

    # D5: store.search() called without filter_dict -> Global Search (confirmed)
    retrieval_config = {
        "metric": "dot_product_on_L2_normalized (cosine equivalent)",
        "embedding_model": index_meta.model_name,
        "embedding_dimension": index_meta.dimension,
        "normalization": index_meta.normalization,
        "index_version": index_meta.index_version,
        "top_k": MAX_K
    }
    
    all_artifacts = []
    
    for i, case in enumerate(cases, 1):
        case_id = case.get('case_id')
        query_text = case.get('query', {}).get('text')
        
        # Fail Fast Policy
        if not case_id or not query_text or 'evidence' not in case:
            print(f"[FAIL FAST] Invalid case JSON: {case_id}")
            sys.exit(1)
            
        target_block_ids = resolve_ground_truth(case, blocks_by_doc)
        if not target_block_ids:
            print(f"[FAIL FAST] Case {case_id} resolved to 0 blocks!")
            sys.exit(1)
            
        retrieved_chunks = run_retrieval(query_text, engine, store, top_k=MAX_K)
        eval_res = evaluate(case_id, target_block_ids, retrieved_chunks, store)
        
        artifact = {
            "run_metadata": run_metadata,
            "retrieval_config": retrieval_config,
            "case_id": case_id,
            "category": case.get('category', 'unknown'),
            "query": query_text,
            "target_block_ids": list(target_block_ids),
            "total_target_blocks": len(target_block_ids),
            "metrics": eval_res['metrics'],
            "top_k_chunks": eval_res['top_k_chunks'],
            "diagnostic_evidence": eval_res['diagnostic_evidence']
        }
        all_artifacts.append(artifact)
        
        m = artifact['metrics']
        print(f"[{i}/{len(cases)}] Case: {case_id} | Target: {len(target_block_ids)} | Cov@{MAX_K}: {m[f'coverage_at_{MAX_K}']*100:.1f}% | MRR_Full: {m['mrr_full_coverage']:.3f}")
        
    num_cases = len(cases)
    
    metrics_sums = {f"coverage_at_{k}": 0.0 for k in K_VALUES}
    metrics_sums['mrr_first_hit'] = 0.0
    metrics_sums['mrr_full_coverage'] = 0.0
    
    for a in all_artifacts:
        for k, v in a['metrics'].items():
            metrics_sums[k] += v
            
    print("\n" + "=" * 50)
    print("FINAL MEAN METRICS (n={})".format(num_cases))
    print("=" * 50)
    for k in K_VALUES:
        print(f"Mean Coverage@{k}:     {metrics_sums[f'coverage_at_{k}'] / num_cases * 100:.2f}%")
    print(f"Mean MRR (First):    {metrics_sums['mrr_first_hit'] / num_cases:.4f}")
    print(f"Mean MRR (Full):     {metrics_sums['mrr_full_coverage'] / num_cases:.4f}")
    print("=" * 50)
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        for a in all_artifacts:
            f.write(json.dumps(a, ensure_ascii=False) + '\n')
    print(f"Exported detailed trace to {OUTPUT_PATH}")
    
    summary_path = os.path.join(os.path.dirname(OUTPUT_PATH), "m4-retrieval-summary.md")
    generate_summary(summary_path, all_artifacts, retrieval_config, run_metadata, num_cases, metrics_sums)
    print(f"Exported summary report to {summary_path}")

if __name__ == "__main__":
    main()
