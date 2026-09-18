import sys
import json
import torch
from sentence_transformers import CrossEncoder
from tqdm import tqdm
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

def run_ce():
    in_file = "evaluation/results/m5_step5_dense_results.json"
    out_file = "evaluation/results/m5_step5_raw_scores.json"
    
    with open(in_file, "r", encoding="utf-8") as f:
        cases = json.load(f)
        
    print(f"Loading Cross-Encoder in fresh process...")
    # Load exactly like Step 4
    ce = CrossEncoder("BAAI/bge-reranker-v2-m3", local_files_only=True, model_kwargs={"torch_dtype": torch.float16})
    
    print("Running CE Inference...")
    for case in tqdm(cases):
        ce_pairs = [[case["query_text"], chunk["text"]] for chunk in case["baseline_chunks"]]
        scores = ce.predict(ce_pairs)
        case["ce_scores_aligned_to_baseline"] = scores.tolist()
        
        # Clean up huge texts
        del case["query_text"]
        del case["baseline_chunks"]
        
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2)
    print(f"Saved final scores to {out_file}")

if __name__ == "__main__":
    run_ce()
