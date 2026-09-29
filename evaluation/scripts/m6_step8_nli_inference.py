import json
import os
import argparse
from transformers import pipeline

def run_nli_inference(input_file, output_file, model_name="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"):
    print(f"Loading NLI model: {model_name}...")
    
    # We use text-classification pipeline which returns all label probabilities
    classifier = pipeline("text-classification", model=model_name, top_k=None)
    
    print(f"Reading dataset from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        cases = [json.loads(line) for line in f]
    
    print(f"Running inference on {len(cases)} cases...")
    
    results = []
    for i, case in enumerate(cases):
        claim = case["claim"]
        evidence = case["evidence_text"]
        
        # NLI typically takes (premise, hypothesis).
        # In our case: premise = evidence, hypothesis = claim
        # Format for HuggingFace text-classification pipeline: `{"text": evidence, "text_pair": claim}`
        inputs = {"text": evidence, "text_pair": claim}
        
        # Run inference
        outputs = classifier(inputs)
        
        # The pipeline returns a list of lists, we take the first element
        # Example output: [{'label': 'LABEL_0', 'score': 0.1}, {'label': 'LABEL_1', 'score': 0.8}, {'label': 'LABEL_2', 'score': 0.1}]
        # For cross-encoder/nli-deberta-v3-small, the labels are usually "contradiction", "entailment", "neutral"
        
        # Ensure we have a list of dicts regardless of pipeline return format
        scores_list = outputs[0] if isinstance(outputs[0], list) else outputs
        
        p_entailment = 0.0
        p_contradiction = 0.0
        p_neutral = 0.0
        
        for item in scores_list:
            label = item['label'].lower()
            score = item['score']
            if 'entailment' in label or label == 'label_1':
                p_entailment = score
            elif 'contradiction' in label or label == 'label_0':
                p_contradiction = score
            elif 'neutral' in label or label == 'label_2':
                p_neutral = score

        case_result = {
            "claim_id": case["claim_id"],
            "claim": claim,
            "evidence_text": evidence,
            "ground_truth_label": case["ground_truth_label"],
            "has_rule_violation": case.get("has_rule_violation", False),
            "nli_probs": {
                "P_E": p_entailment,
                "P_N": p_neutral,
                "P_C": p_contradiction
            }
        }
        results.append(case_result)
        
        if (i + 1) % 5 == 0:
            print(f"  Processed {i + 1}/{len(cases)} cases")
            
    # Write to output JSONL
    print(f"Writing results to {output_file}...")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for res in results:
            f.write(json.dumps(res, ensure_ascii=False) + '\n')
            
    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="evaluation/datasets/m6_check3_claim_grounding.jsonl")
    parser.add_argument("--output", type=str, default="evaluation/results/m6_check3_raw_nli_scores.jsonl")
    parser.add_argument("--model", type=str, default="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
    args = parser.parse_args()
    
    run_nli_inference(args.input, args.output, args.model)
