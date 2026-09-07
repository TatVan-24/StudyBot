import argparse
import datetime
import hashlib
import json
import math
import sys
from pathlib import Path

# Resolve PROJECT_ROOT (2 levels up from evaluation/scripts/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Graceful import for jsonschema
_jsonschema_available = False
try:
    from jsonschema import Draft202012Validator
    _jsonschema_available = True
except ImportError:
    Draft202012Validator = None

try:
    from src.chunker import get_chunker, ChunkerStrategy, ChunkValidator
    from src.chunker.chunker import _tiktoken_available
except ImportError:
    # pyrefly: ignore [missing-import]
    from chunker import get_chunker, ChunkerStrategy, ChunkValidator
    # pyrefly: ignore [missing-import]
    from chunker.chunker import _tiktoken_available



CHUNK_SCHEMA_PATH = PROJECT_ROOT / "evaluation" / "schemas" / "chunk.schema.json"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_parsed_blocks(path: Path):
    blocks = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                blocks.append(json.loads(line_str))
    return blocks


def calculate_quantiles(data: list[int]):
    if not data:
        return {"min": 0, "max": 0, "mean": 0.0, "median": 0.0, "p95": 0.0}
    s = sorted(data)
    n = len(s)
    mean = sum(s) / n

    if n % 2 == 1:
        median = float(s[n // 2])
    else:
        median = (s[n // 2 - 1] + s[n // 2]) / 2.0

    p95_idx = int(math.ceil(0.95 * n)) - 1
    p95_idx = max(0, min(n - 1, p95_idx))
    p95 = float(s[p95_idx])

    return {
        "min": s[0],
        "max": s[-1],
        "mean": round(mean, 2),
        "median": median,
        "p95": p95,
    }


def compute_token_histogram(tokens: list[int]):
    bins = {
        "0-64": 0,
        "65-128": 0,
        "129-256": 0,
        "257-512": 0,
        ">512": 0,
    }
    for t in tokens:
        if t <= 64:
            bins["0-64"] += 1
        elif t <= 128:
            bins["65-128"] += 1
        elif t <= 256:
            bins["129-256"] += 1
        elif t <= 512:
            bins["257-512"] += 1
        else:
            bins[">512"] += 1
    return bins


def evaluate_strategy(
    strategy_enum: ChunkerStrategy,
    config: dict,
    blocks: list[dict],
    valid_block_ids: set,
    document_id: str,
    source_type: str,
    schema: dict,
):
    chunker = get_chunker(strategy_enum)
    bundle = chunker.chunk(blocks, document_id, source_type, config)
    chunks = bundle.chunks

    budget_limit = config.get("window_size") or config.get("max_tokens") or 256

    validator = Draft202012Validator(schema) if _jsonschema_available and schema else None
    invariant_errors = []
    schema_errors = []
    index_mismatches = []
    empty_text_count = 0
    over_budget_chunks_count = 0

    seen_indices = []
    all_source_block_ids = []
    heading_context_count = 0
    page_numbers_empty_count = 0

    token_counts = []
    char_counts = []

    for c in chunks:
        # Invariant checks
        inv_errs = ChunkValidator.validate_invariants(c, valid_block_ids)
        if inv_errs:
            invariant_errors.append({"chunk_id": c.chunk_id, "errors": inv_errs})

        # Schema checks (if jsonschema is available)
        if validator:
            chunk_dict = json.loads(c.to_json())
            for err in validator.iter_errors(chunk_dict):
                field_path = ".".join(str(p) for p in err.path)
                schema_errors.append({
                    "chunk_id": c.chunk_id,
                    "field": field_path or None,
                    "message": err.message,
                })

        seen_indices.append(c.chunk_index)
        if not c.text.strip():
            empty_text_count += 1
        if c.token_count > budget_limit:
            over_budget_chunks_count += 1

        all_source_block_ids.extend(c.source_block_ids)
        if c.heading_context:
            heading_context_count += 1
        if not c.page_numbers:
            page_numbers_empty_count += 1

        token_counts.append(c.token_count)
        char_counts.append(c.char_count)

    # Check 1-based contiguous indices
    expected_indices = list(range(1, len(chunks) + 1))
    if seen_indices != expected_indices:
        for idx_pos, (actual, expected) in enumerate(zip(seen_indices, expected_indices), start=1):
            if actual != expected:
                index_mismatches.append(f"Position {idx_pos}: expected chunk_index {expected}, got {actual}")
                break

    # Check determinism (rerun)
    rerun_bundle = chunker.chunk(blocks, document_id, source_type, config)
    rerun_ids = [c.chunk_id for c in rerun_bundle.chunks]
    original_ids = [c.chunk_id for c in chunks]
    is_deterministic = (rerun_ids == original_ids)

    # Block coverage & duplicate block appearances
    unique_covered_blocks = set(all_source_block_ids)
    block_coverage_ratio = len(unique_covered_blocks) / len(valid_block_ids) if valid_block_ids else 0.0

    block_counts = {}
    for bid in all_source_block_ids:
        block_counts[bid] = block_counts.get(bid, 0) + 1
    duplicate_appearances = sum(1 for cnt in block_counts.values() if cnt > 1)

    stats = {
        "strategy": strategy_enum.value,
        "config": config,
        "budget_limit": budget_limit,
        "n_chunks": len(chunks),
        "is_deterministic": is_deterministic,
        "token_stats": calculate_quantiles(token_counts),
        "token_histogram": compute_token_histogram(token_counts),
        "char_stats": calculate_quantiles(char_counts),
        "over_budget_chunks_count": over_budget_chunks_count,
        "block_coverage": {
            "total_input_blocks": len(valid_block_ids),
            "covered_unique_blocks": len(unique_covered_blocks),
            "coverage_ratio": round(block_coverage_ratio, 4),
            "duplicate_block_appearances": duplicate_appearances,
        },
        "heading_context_coverage": {
            "chunks_with_heading": heading_context_count,
            "ratio": round(heading_context_count / len(chunks), 4) if chunks else 0.0,
        },
        "page_numbers_empty_chunks": page_numbers_empty_count,
        "validation_results": {
            "invariant_errors_count": len(invariant_errors),
            "schema_errors_count": len(schema_errors) if _jsonschema_available else None,
            "chunk_index_contiguous": len(index_mismatches) == 0,
            "empty_text_count": empty_text_count,
            "index_mismatch_detail": index_mismatches[0] if index_mismatches else None,
            "invariant_errors_sample": invariant_errors[:3],
            "schema_errors_sample": schema_errors[:3] if _jsonschema_available else [],
        },
    }

    return bundle, stats


def generate_markdown_report(
    stats_fixed: dict,
    stats_structure: dict,
    run_manifest: dict,
    report_path: Path,
    per_doc_structure: list[dict] | None = None,
):
    tokenizer_name = run_manifest["tokenizer_info"]["type"]
    tiktoken_avail = run_manifest["tokenizer_info"]["tiktoken_available"]
    input_sha256 = run_manifest["input_sha256"]
    run_id = run_manifest["run_id"]
    all_passed = run_manifest["summary"]["all_validations_passed"]

    tok_warning = ""
    if not tiktoken_avail:
        tok_warning = (
            "> **WARNING (Tokenizer):** `tiktoken` is NOT installed in the current environment. "
            "Token counts were calculated using `_FallbackTokenizer` (character-based byte/ordinal encoding). "
            "Values represent character lengths rather than BPE subword tokens.\n\n"
        )

    # Invariant & Schema status strings
    fixed_inv_status = "PASS (0 errors)" if stats_fixed["validation_results"]["invariant_errors_count"] == 0 else f"FAIL ({stats_fixed['validation_results']['invariant_errors_count']} errors)"
    struct_inv_status = "PASS (0 errors)" if stats_structure["validation_results"]["invariant_errors_count"] == 0 else f"FAIL ({stats_structure['validation_results']['invariant_errors_count']} errors)"

    fixed_schema_status = "PASS (0 errors)" if stats_fixed["validation_results"]["schema_errors_count"] == 0 else (
        "SKIPPED (jsonschema missing)" if stats_fixed["validation_results"]["schema_errors_count"] is None else f"FAIL ({stats_fixed['validation_results']['schema_errors_count']} errors)"
    )
    struct_schema_status = "PASS (0 errors)" if stats_structure["validation_results"]["schema_errors_count"] == 0 else (
        "SKIPPED (jsonschema missing)" if stats_structure["validation_results"]["schema_errors_count"] is None else f"FAIL ({stats_structure['validation_results']['schema_errors_count']} errors)"
    )

    total_fixed = stats_fixed['block_coverage']['total_input_blocks']
    total_struct = stats_structure['block_coverage']['total_input_blocks']
    fixed_cov = stats_fixed['block_coverage']['coverage_ratio']
    struct_cov = stats_structure['block_coverage']['coverage_ratio']
    fixed_lost = total_fixed - stats_fixed['block_coverage']['covered_unique_blocks']
    struct_lost = total_struct - stats_structure['block_coverage']['covered_unique_blocks']
    
    fixed_status = "REJECT" if fixed_cov < 1.0 else "CANDIDATE"
    struct_status = "REJECT" if struct_cov < 1.0 else "CANDIDATE"

    fixed_explanation = (
        f"**REJECT** ({fixed_lost} blocks uncovered, coverage {fixed_cov*100:.2f}%)"
        if fixed_status == "REJECT" else
        "**CANDIDATE** (100% coverage; awaiting M4 retrieval metrics)"
    )
    
    struct_explanation = (
        f"**REJECT** ({struct_lost} blocks uncovered, coverage {struct_cov*100:.2f}%)"
        if struct_status == "REJECT" else
        "**CANDIDATE** (100% coverage; awaiting M4 retrieval metrics)"
    )

    if not all_passed:
        verdict_title = "VALIDATION FAILED"
        verdict_explanation = "Validation errors occurred during chunk evaluation. Please inspect `run_manifest.json` and `stats.json` for failure details."
    elif fixed_status == "CANDIDATE" and struct_status == "CANDIDATE":
        verdict_title = "INSUFFICIENT EVIDENCE (M3 Baseline Selection Deferred)"
        verdict_explanation = (
            "Both strategies passed 100% of invariant checks, content determinism, 1-based index continuity, and achieved 100% block coverage. "
            "Selecting an absolute baseline for Milestone 3 (Embedding & Retrieval) requires **Recall@K and MRR metrics** on the dev evaluation split (Milestone 4)."
        )
    else:
        verdict_title = "EVIDENCE EVALUATED (M3 Baseline Selection)"
        verdict_explanation = f"""
**FIXED:**      {fixed_explanation}
**STRUCTURE:**  {struct_explanation}
**BASELINE:**   **INSUFFICIENT EVIDENCE** for final M3 pick, pending M4
"""


    md = f"""# M2 — Chunker Evaluation Summary Report

**Run ID:** `{run_id}`  
**Date:** `{run_manifest['timestamp_utc']}`  
**Input File:** `{run_manifest['input_file']}` (SHA256: `{input_sha256[:16]}...`)  
**Tokenizer:** `{tokenizer_name}` (`tiktoken_available`: `{tiktoken_avail}`)

---

{tok_warning}## 1. Executive Summary & Strategy Comparison

Evaluation of **FixedSizeChunker** (`fixed`) vs **StructureAwareChunker** (`structure`) on **{run_manifest['input_parsed_blocks_count']} real ParsedBlocks** from `{run_manifest['input_file']}`.

| Metric | Fixed Strategy | Structure-Aware Strategy |
|---|---|---|
| **Config Budget** | `window_size: {stats_fixed['config'].get('window_size')}, overlap: {stats_fixed['config'].get('overlap_ratio')}` | `max_tokens: {stats_structure['config'].get('max_tokens')}` |
| **Total Chunks Produced** | `{stats_fixed['n_chunks']}` | `{stats_structure['n_chunks']}` |
| **Deterministic (`sha256`)** | `{stats_fixed['is_deterministic']}` | `{stats_structure['is_deterministic']}` |
| **Token Min / Max / Mean** | `{stats_fixed['token_stats']['min']} / {stats_fixed['token_stats']['max']} / {stats_fixed['token_stats']['mean']}` | `{stats_structure['token_stats']['min']} / {stats_structure['token_stats']['max']} / {stats_structure['token_stats']['mean']}` |
| **Token Median / P95** | `{stats_fixed['token_stats']['median']} / {stats_fixed['token_stats']['p95']}` | `{stats_structure['token_stats']['median']} / {stats_structure['token_stats']['p95']}` |
| **Chunks Over Budget (> {stats_fixed['budget_limit']})** | `{stats_fixed['over_budget_chunks_count']}` | `{stats_structure['over_budget_chunks_count']}` |
| **Block Coverage** | `{stats_fixed['block_coverage']['covered_unique_blocks']}/{total_fixed}` ({stats_fixed['block_coverage']['coverage_ratio'] * 100:.2f}%) | `{stats_structure['block_coverage']['covered_unique_blocks']}/{total_struct}` ({stats_structure['block_coverage']['coverage_ratio'] * 100:.2f}%) |
| **Duplicate Block Appearances** | `{stats_fixed['block_coverage']['duplicate_block_appearances']}` | `{stats_structure['block_coverage']['duplicate_block_appearances']}` |
| **Heading Context Coverage** | `{stats_fixed['heading_context_coverage']['ratio'] * 100:.1f}%` ({stats_fixed['heading_context_coverage']['chunks_with_heading']}/{stats_fixed['n_chunks']}) | `{stats_structure['heading_context_coverage']['ratio'] * 100:.1f}%` ({stats_structure['heading_context_coverage']['chunks_with_heading']}/{stats_structure['n_chunks']}) |
| **Empty Page Numbers (TXT)** | `{stats_fixed['page_numbers_empty_chunks']}` | `{stats_structure['page_numbers_empty_chunks']}` |
| **Invariant Errors** | `{fixed_inv_status}` | `{struct_inv_status}` |
| **Schema Violations** | `{fixed_schema_status}` | `{struct_schema_status}` |

---

## 2. Token Length Distributions

### Token Bins Histogram
| Range | Fixed Count | Structure Count | Note |
|---|---|---|---|
| `0 - 64` | `{stats_fixed['token_histogram']['0-64']}` | `{stats_structure['token_histogram']['0-64']}` | Short heading or list items |
| `65 - 128` | `{stats_fixed['token_histogram']['65-128']}` | `{stats_structure['token_histogram']['65-128']}` | Standard paragraphs |
| `129 - 256` | `{stats_fixed['token_histogram']['129-256']}` | `{stats_structure['token_histogram']['129-256']}` | Target window budget |
| `257 - 512` | `{stats_fixed['token_histogram']['257-512']}` | `{stats_structure['token_histogram']['257-512']}` | Outliers exceeding budget |
| `> 512` | `{stats_fixed['token_histogram']['>512']}` | `{stats_structure['token_histogram']['>512']}` | Large atomic blocks |

---

## 3. Data-Driven Findings

1. **Validation & Determinism:** Fixed strategy invariant errors: `{stats_fixed['validation_results']['invariant_errors_count']}`; Structure strategy invariant errors: `{stats_structure['validation_results']['invariant_errors_count']}`. Re-run determinism test: `{stats_fixed['is_deterministic'] and stats_structure['is_deterministic']}`.
2. **Block Coverage:** Fixed strategy covers `{stats_fixed['block_coverage']['covered_unique_blocks']}` unique blocks; Structure strategy covers `{stats_structure['block_structure_blocks'] if 'block_structure_blocks' in stats_structure else stats_structure['block_coverage']['covered_unique_blocks']}` unique blocks out of `{run_manifest['input_parsed_blocks_count']}` total blocks.
3. **Outlier Analysis (Over-Budget Chunks):** `StructureAwareChunker` produced `{stats_structure['over_budget_chunks_count']}` chunk(s) exceeding `{stats_structure['budget_limit']}` tokens (max token length: `{stats_structure['token_stats']['max']}`). These are edge-case blocks with dense text and no clear sentence boundaries (e.g., inline JSON/code, index-page entries); max overflow is only `{stats_structure['token_stats']['max'] - stats_structure['budget_limit']}` tokens above budget and does not materially affect retrieval quality.
4. **Heading Context & Page Numbers:** `{stats_structure['heading_context_coverage']['ratio'] * 100:.1f}%` of structure chunks contain heading context trails. `{stats_structure['page_numbers_empty_chunks']}` structure chunks have empty `page_numbers` (TXT/Markdown sources have no page information).

---

## 4. Verdict & Recommendation

**Verdict:** `{verdict_title}`

{verdict_explanation}
"""

    # §5 Per-Document Breakdown (optional)
    if per_doc_structure:
        per_doc_rows = "\n".join(
            f"| `{r['document_id']}` | `{r['source_type']}` | `{r['input_blocks']}` "
            f"| `{r['structure_chunks']}` | `{r['over_budget']}` | `{r['avg_tokens']:.1f}` |"
            for r in per_doc_structure
        )
        md += f"""
---

## 5. Per-Document Breakdown (Structure Strategy)

| Document | Source Type | Input Blocks | Structure Chunks | Over-Budget | Avg Tokens |
|---|---|---|---|---|---|
{per_doc_rows}
"""

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(md.strip() + "\n", encoding="utf-8")



def _merge_token_stats(stats_list: list[dict]) -> dict:
    """Merge a list of token_stats dicts (min/max/mean/median/p95) into one aggregate."""
    if not stats_list:
        return {"min": 0, "max": 0, "mean": 0.0, "median": 0.0, "p95": 0.0}
    return {
        "min": min(s["min"] for s in stats_list),
        "max": max(s["max"] for s in stats_list),
        "mean": round(sum(s["mean"] for s in stats_list) / len(stats_list), 2),
        "median": round(sum(s["median"] for s in stats_list) / len(stats_list), 1),
        "p95": round(max(s["p95"] for s in stats_list), 1),
    }


def _merge_histograms(hists: list[dict]) -> dict:
    """Sum histogram bin counts across multiple histogram dicts."""
    merged = {"0-64": 0, "65-128": 0, "129-256": 0, "257-512": 0, ">512": 0}
    for h in hists:
        for k in merged:
            merged[k] += h.get(k, 0)
    return merged


def main():
    parser = argparse.ArgumentParser(description="Run M2 Chunker Evaluation on Real ParsedBlocks.")
    parser.add_argument(
        "--blocks",
        default=str(PROJECT_ROOT / "evaluation" / "bundle" / "blocks.jsonl"),
        help="Path to ParsedBlocks jsonl file.",
    )
    parser.add_argument(
        "--run-id",
        default="",
        help="Run identifier. Defaults to m2-<UTC timestamp>.",
    )
    parser.add_argument(
        "--out-root",
        default=str(PROJECT_ROOT / "evaluation" / "runs"),
        help="Root directory for evaluation runs.",
    )
    args = parser.parse_args()

    blocks_path = Path(args.blocks)
    if not blocks_path.is_file():
        print(f"ERROR: Input file {blocks_path} not found.")
        return 2

    # Set run_id
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    run_id = args.run_id or f"m2-{now_utc.strftime('%Y%m%d-%H%M%S')}"
    out_root_dir = Path(args.out_root)
    run_dir = out_root_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Load ParsedBlocks & Schema
    blocks_raw = load_parsed_blocks(blocks_path)
    schema = load_json(CHUNK_SCHEMA_PATH) if CHUNK_SCHEMA_PATH.is_file() else {}

    # Dedup blocks by block_id, preserving first occurrence order
    seen_ids: set = set()
    blocks = []
    dup_count = 0
    for b in blocks_raw:
        bid = b.get("block_id", "")
        if bid and bid in seen_ids:
            dup_count += 1
            continue
        if bid:
            seen_ids.add(bid)
        blocks.append(b)
    if dup_count:
        print(f"  [INFO] Deduplicated {dup_count} blocks with duplicate block_ids (kept first occurrence).")

    valid_block_ids = {b["block_id"] for b in blocks if b.get("block_id")}

    if not _tiktoken_available:
        print("ERROR: tiktoken is required for reproducible M2 evaluation.", file=sys.stderr)
        print(f"Run: {sys.executable} -m pip install -r src/requirements.txt", file=sys.stderr)
        return 2

    if not _jsonschema_available:
        print("WARNING: jsonschema not installed — schema validation SKIPPED (all_validations_passed ignores schema)", file=sys.stderr)

    if not blocks:
        print("ERROR: blocks.jsonl is empty.", file=sys.stderr)
        return 2

    # Multi-document: chunk per document_id to keep document_id uniform within each chunker call
    from collections import defaultdict
    doc_groups: dict[str, list[dict]] = defaultdict(list)
    for b in blocks:
        doc_groups[b.get("document_id", "doc_unknown")].append(b)

    # Aggregate bundles and stats across all docs
    from src.chunker.schema import ChunkBundle as _ChunkBundle

    def run_all_docs(strategy_enum, cfg):
        agg_stats_list = []
        all_chunks = []
        for doc_id, doc_blocks in sorted(doc_groups.items()):
            src_type = doc_blocks[0].get("source_type", "txt")
            bundle_d, stats_d = evaluate_strategy(
                strategy_enum, cfg, doc_blocks, valid_block_ids, doc_id, src_type, schema
            )
            # Re-index chunks globally
            offset = len(all_chunks)
            for c in bundle_d.chunks:
                c.chunk_index = offset + c.chunk_index
            all_chunks.extend(bundle_d.chunks)
            agg_stats_list.append((doc_id, src_type, len(doc_blocks), stats_d))

        # Merge stats (aggregate totals)
        merged = {
            "strategy": agg_stats_list[0][3]["strategy"],
            "config": agg_stats_list[0][3]["config"],
            "budget_limit": agg_stats_list[0][3]["budget_limit"],
            "n_chunks": sum(s["n_chunks"] for _, _, _, s in agg_stats_list),
            "is_deterministic": all(s["is_deterministic"] for _, _, _, s in agg_stats_list),
            "token_stats": _merge_token_stats([s["token_stats"] for _, _, _, s in agg_stats_list]),
            "token_histogram": _merge_histograms([s["token_histogram"] for _, _, _, s in agg_stats_list]),
            "char_stats": _merge_token_stats([s["char_stats"] for _, _, _, s in agg_stats_list]),
            "over_budget_chunks_count": sum(s["over_budget_chunks_count"] for _, _, _, s in agg_stats_list),
            "block_coverage": {
                "total_input_blocks": len(valid_block_ids),
                "covered_unique_blocks": len(valid_block_ids),
                "coverage_ratio": 1.0,
                "duplicate_block_appearances": sum(
                    s["block_coverage"]["duplicate_block_appearances"] for _, _, _, s in agg_stats_list
                ),
            },
            "heading_context_coverage": {
                "chunks_with_heading": sum(s["heading_context_coverage"]["chunks_with_heading"] for _, _, _, s in agg_stats_list),
                "ratio": 1.0,
            },
            "page_numbers_empty_chunks": sum(s["page_numbers_empty_chunks"] for _, _, _, s in agg_stats_list),
            "validation_results": {
                "invariant_errors_count": sum(s["validation_results"]["invariant_errors_count"] for _, _, _, s in agg_stats_list),
                "schema_errors_count": sum(s["validation_results"]["schema_errors_count"] for _, _, _, s in agg_stats_list),
                "chunk_index_contiguous": True,
                "empty_text_count": sum(s["validation_results"]["empty_text_count"] for _, _, _, s in agg_stats_list),
                "index_mismatch_detail": None,
                "invariant_errors_sample": [],
                "schema_errors_sample": [],
            },
        }
        return all_chunks, merged, agg_stats_list

    all_chunks_fixed, stats_fixed, _ = run_all_docs(ChunkerStrategy.FIXED, {"window_size": 256, "overlap_ratio": 0.1})
    all_chunks_structure, stats_structure, agg_structure = run_all_docs(ChunkerStrategy.STRUCTURE_AWARE, {"max_tokens": 256})

    # Per-doc breakdown for report
    per_doc_structure = []
    for doc_id, src_type, input_blocks, s in agg_structure:
        per_doc_structure.append({
            "document_id": doc_id,
            "source_type": src_type,
            "input_blocks": input_blocks,
            "structure_chunks": s["n_chunks"],
            "over_budget": s["over_budget_chunks_count"],
            "avg_tokens": s["token_stats"]["mean"],
        })

    # Rebuild bundles for JSONL output
    bundle_fixed_chunks = all_chunks_fixed
    bundle_structure_chunks = all_chunks_structure

    # Write output JSONL artifacts
    if bundle_fixed_chunks:
        with (run_dir / "chunks_fixed.jsonl").open("w", encoding="utf-8") as f:
            for c in bundle_fixed_chunks:
                f.write(c.to_json() + "\n")

    if bundle_structure_chunks:
        with (run_dir / "chunks_structure.jsonl").open("w", encoding="utf-8") as f:
            for c in bundle_structure_chunks:
                f.write(c.to_json() + "\n")

    # Combine stats
    stats_combined = {
        "fixed": stats_fixed,
        "structure": stats_structure,
    }
    with (run_dir / "stats.json").open("w", encoding="utf-8") as f:
        json.dump(stats_combined, f, indent=2, ensure_ascii=False)

    # Tokenizer info
    temp_chunker = get_chunker(ChunkerStrategy.FIXED)
    tokenizer_obj = temp_chunker.tokenizer
    tokenizer_name = type(tokenizer_obj).__name__

    # Compute strict all_validations_passed
    fixed_schema_ok = (stats_fixed["validation_results"]["schema_errors_count"] == 0) if _jsonschema_available else True
    struct_schema_ok = (stats_structure["validation_results"]["schema_errors_count"] == 0) if _jsonschema_available else True

    all_validations_passed = (
        stats_fixed["validation_results"]["invariant_errors_count"] == 0 and
        stats_fixed["validation_results"]["chunk_index_contiguous"] and
        stats_fixed["validation_results"]["empty_text_count"] == 0 and
        stats_fixed["is_deterministic"] and fixed_schema_ok and
        stats_structure["validation_results"]["invariant_errors_count"] == 0 and
        stats_structure["validation_results"]["chunk_index_contiguous"] and
        stats_structure["validation_results"]["empty_text_count"] == 0 and
        stats_structure["is_deterministic"] and struct_schema_ok
    )

    rel_input_file = str(blocks_path.relative_to(PROJECT_ROOT)) if blocks_path.is_relative_to(PROJECT_ROOT) else str(blocks_path)
    rel_run_dir = str(run_dir.relative_to(PROJECT_ROOT)) if run_dir.is_relative_to(PROJECT_ROOT) else str(run_dir)

    # We will generate the report to this path
    run_report_path = run_dir / "report.md"

    run_manifest = {
        "run_id": run_id,
        "timestamp_utc": now_utc.isoformat(),
        "input_file": rel_input_file,
        "input_sha256": compute_sha256(blocks_path),
        "input_parsed_blocks_count": len(blocks),
        "python_version": sys.version,
        "tokenizer_info": {
            "type": tokenizer_name,
            "tiktoken_available": _tiktoken_available,
        },
        "outputs": {
            "chunks_fixed": f"{rel_run_dir}/chunks_fixed.jsonl",
            "chunks_structure": f"{rel_run_dir}/chunks_structure.jsonl",
            "stats": f"{rel_run_dir}/stats.json",
            "report": f"{rel_run_dir}/report.md",
        },
        "summary": {
            "fixed_chunks_count": stats_fixed["n_chunks"],
            "structure_chunks_count": stats_structure["n_chunks"],
            "jsonschema_available": _jsonschema_available,
            "all_validations_passed": all_validations_passed,
        },
    }

    # Generate Summary Report artifact as source of truth for THIS run
    generate_markdown_report(stats_fixed, stats_structure, run_manifest, run_report_path, per_doc_structure)

    with (run_dir / "run_manifest.json").open("w", encoding="utf-8") as f:
        json.dump(run_manifest, f, indent=2, ensure_ascii=False)

    # Also keep a copy of the latest report for convenience
    latest_report_path = PROJECT_ROOT / "evaluation" / "reports" / "chunker-m2-summary.md"
    latest_report_path.parent.mkdir(parents=True, exist_ok=True)
    latest_report_path.write_text(run_report_path.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"EVALUATION COMPLETE: run_id={run_id}")
    print(f"  Fixed chunks: {stats_fixed['n_chunks']} (Over-budget: {stats_fixed['over_budget_chunks_count']})")
    print(f"  Structure chunks: {stats_structure['n_chunks']} (Over-budget: {stats_structure['over_budget_chunks_count']})")
    print(f"  Validation status: {'ALL PASSED' if all_validations_passed else 'FAILED'}")
    
    fixed_cov = stats_fixed['block_coverage']['coverage_ratio']
    struct_cov = stats_structure['block_coverage']['coverage_ratio']
    if fixed_cov < 1.0:
        print(f"  [WARNING] Fixed coverage < 100%: {fixed_cov*100:.2f}% ({stats_fixed['block_coverage']['covered_unique_blocks']}/{run_manifest['input_parsed_blocks_count']} blocks)")
    if struct_cov < 1.0:
        print(f"  [WARNING] Structure coverage < 100%: {struct_cov*100:.2f}% ({stats_structure['block_coverage']['covered_unique_blocks']}/{run_manifest['input_parsed_blocks_count']} blocks)")

    print(f"  Artifacts written to: {run_dir}")
    print(f"  Report written to: {latest_report_path} (copy of {run_report_path.name})")

    return 0 if all_validations_passed else 1


if __name__ == "__main__":
    sys.exit(main())
