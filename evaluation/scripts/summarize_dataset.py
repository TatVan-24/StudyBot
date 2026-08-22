"""Summarize StudyBot Evaluation Dataset v1 and detect split leakage."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


EVALUATION_ROOT = Path(__file__).resolve().parents[1]

PUBLIC_MANIFEST = (
    EVALUATION_ROOT / "corpus" / "manifest.public.jsonl"
)

DEVELOPMENT_DATASET = (
    EVALUATION_ROOT / "datasets" / "development-v1.jsonl"
)

TEST_DATASET = (
    EVALUATION_ROOT / "datasets" / "test-v1.jsonl"
)

REPORT_PATH = (
    EVALUATION_ROOT / "reports" / "dataset-v1-summary.md"
)

EXPECTED_CATEGORIES = {
    "direct_factual",
    "multi_section_synthesis",
    "multi_document_synthesis",
    "lexical_mismatch",
    "cross_document_confusion",
    "unanswerable",
    "cross_lingual",
    "table_or_visual_limitation",
}

EXPECTED_SPLIT_COUNTS = {
    "development": 30,
    "test": 10,
}

FACT_SIMILARITY_WARNING_THRESHOLD = 0.65


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            if not raw_line.strip():
                continue

            try:
                row = json.loads(raw_line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"{path}:{line_number}: invalid JSON: {error.msg}"
                ) from error

            if not isinstance(row, dict):
                raise ValueError(
                    f"{path}:{line_number}: entry must be a JSON object"
                )

            rows.append(row)

    return rows


def markdown_table(
    headers: list[str],
    rows: list[list[Any]],
) -> str:
    output = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]

    for row in rows:
        cells = [
            str(value).replace("|", "\\|").replace("\n", " ")
            for value in row
        ]
        output.append("| " + " | ".join(cells) + " |")

    return "\n".join(output)


def normalize_text(text: str) -> set[str]:
    tokens = re.findall(
        r"[a-zA-ZÀ-ỹ0-9]+",
        text.lower(),
    )

    stopwords = {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "to",
        "of",
        "in",
        "on",
        "for",
        "and",
        "or",
        "that",
        "this",
        "what",
        "which",
        "how",
        "according",
        "document",
        "source",
        "it",
        "its",
    }

    return {
        token
        for token in tokens
        if token not in stopwords and len(token) > 1
    }


def jaccard_similarity(
    first: set[str],
    second: set[str],
) -> float:
    if not first or not second:
        return 0.0

    return len(first & second) / len(first | second)


def case_fact_text(case: dict[str, Any]) -> str:
    expected = case.get("expected", {})

    reference_answer = expected.get("reference_answer") or ""
    required_facts = expected.get("required_facts", [])

    return " ".join(
        [reference_answer, *required_facts]
    )


def locator_description(locator: dict[str, Any]) -> str:
    locator_type = locator.get("type")

    if locator_type == "page":
        description = f"PDF page {locator.get('pdf_page')}"

        if locator.get("printed_page") is not None:
            description += (
                f" / printed page {locator['printed_page']}"
            )

        if locator.get("section"):
            description += f" / {locator['section']}"

        return description

    if locator_type == "slide":
        description = f"Slide {locator.get('slide')}"

        if locator.get("title"):
            description += f" / {locator['title']}"

        return description

    if locator_type == "section":
        return " > ".join(
            locator.get("heading_path", [])
        )

    if locator_type == "paragraph":
        return (
            f"Paragraph {locator.get('paragraph_index')}"
        )

    if locator_type == "text_span":
        return (
            f"Lines {locator.get('start_line')}"
            f"–{locator.get('end_line')}"
        )

    return json.dumps(locator, ensure_ascii=False)


def locators_overlap(
    first: dict[str, Any],
    second: dict[str, Any],
) -> bool:
    first_type = first.get("type")
    second_type = second.get("type")

    if first_type != second_type:
        return False

    if first_type == "page":
        return (
            first.get("pdf_page")
            == second.get("pdf_page")
        )

    if first_type == "slide":
        return (
            first.get("slide")
            == second.get("slide")
        )

    if first_type == "paragraph":
        return (
            first.get("paragraph_index")
            == second.get("paragraph_index")
        )

    if first_type == "section":
        first_path = first.get("heading_path", [])
        second_path = second.get("heading_path", [])

        return (
            first_path == second_path
            or first_path[: len(second_path)] == second_path
            or second_path[: len(first_path)] == first_path
        )

    if first_type == "text_span":
        first_start = first.get("start_line")
        first_end = first.get("end_line")
        second_start = second.get("start_line")
        second_end = second.get("end_line")

        if not all(
            isinstance(value, int)
            for value in (
                first_start,
                first_end,
                second_start,
                second_end,
            )
        ):
            return False

        return max(first_start, second_start) <= min(
            first_end,
            second_end,
        )

    return False


def find_evidence_leakage(
    development_cases: list[dict[str, Any]],
    test_cases: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    for development_case in development_cases:
        for test_case in test_cases:
            for development_evidence in development_case.get(
                "evidence", []
            ):
                for test_evidence in test_case.get(
                    "evidence", []
                ):
                    document_id = development_evidence.get(
                        "document_id"
                    )

                    if (
                        document_id
                        != test_evidence.get("document_id")
                    ):
                        continue

                    development_locator = (
                        development_evidence.get(
                            "locator", {}
                        )
                    )

                    test_locator = test_evidence.get(
                        "locator", {}
                    )

                    if locators_overlap(
                        development_locator,
                        test_locator,
                    ):
                        findings.append(
                            {
                                "document_id": document_id,
                                "development_case": (
                                    development_case["case_id"]
                                ),
                                "test_case": (
                                    test_case["case_id"]
                                ),
                                "development_locator": (
                                    locator_description(
                                        development_locator
                                    )
                                ),
                                "test_locator": (
                                    locator_description(
                                        test_locator
                                    )
                                ),
                            }
                        )

    return findings


def find_fact_similarity(
    development_cases: list[dict[str, Any]],
    test_cases: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    for development_case in development_cases:
        development_documents = set(
            development_case.get(
                "scope", {}
            ).get("document_ids", [])
        )

        development_tokens = normalize_text(
            case_fact_text(development_case)
        )

        if not development_tokens:
            continue

        for test_case in test_cases:
            test_documents = set(
                test_case.get(
                    "scope", {}
                ).get("document_ids", [])
            )

            if not (
                development_documents & test_documents
            ):
                continue

            test_tokens = normalize_text(
                case_fact_text(test_case)
            )

            similarity = jaccard_similarity(
                development_tokens,
                test_tokens,
            )

            if (
                similarity
                >= FACT_SIMILARITY_WARNING_THRESHOLD
            ):
                findings.append(
                    {
                        "development_case": (
                            development_case["case_id"]
                        ),
                        "test_case": test_case["case_id"],
                        "similarity": similarity,
                        "shared_documents": ", ".join(
                            sorted(
                                development_documents
                                & test_documents
                            )
                        ),
                    }
                )

    return sorted(
        findings,
        key=lambda finding: finding["similarity"],
        reverse=True,
    )


def count_documents(
    cases: list[dict[str, Any]],
) -> Counter[str]:
    counter: Counter[str] = Counter()

    for case in cases:
        for document_id in case.get(
            "scope", {}
        ).get("document_ids", []):
            counter[document_id] += 1

    return counter


def main() -> int:
    manifest = read_jsonl(PUBLIC_MANIFEST)
    development_cases = read_jsonl(
        DEVELOPMENT_DATASET
    )
    test_cases = read_jsonl(TEST_DATASET)

    all_cases = development_cases + test_cases

    ground_truth_documents = {
        entry["document_id"]
        for entry in manifest
        if entry.get("corpus_role") == "GROUND_TRUTH"
    }

    split_counts = Counter(
        case["split"]
        for case in all_cases
    )

    category_counts = Counter(
        case["category"]
        for case in all_cases
    )

    language_counts = Counter(
        case["query"]["language"]
        for case in all_cases
    )

    answerability_counts = Counter(
        case["expected"]["answerability"]
        for case in all_cases
    )

    review_counts = Counter(
        case["review"]["status"]
        for case in all_cases
    )

    document_counts = count_documents(all_cases)

    evidence_leakage = find_evidence_leakage(
        development_cases,
        test_cases,
    )

    fact_similarity = find_fact_similarity(
        development_cases,
        test_cases,
    )

    query_counts = Counter(
        case["query"]["text"].strip().lower()
        for case in all_cases
    )

    duplicate_queries = sorted(
        query
        for query, count in query_counts.items()
        if count > 1
    )

    missing_categories = sorted(
        EXPECTED_CATEGORIES - set(category_counts)
    )

    unused_documents = sorted(
        ground_truth_documents - set(document_counts)
    )

    blockers: list[str] = []
    warnings: list[str] = []

    if len(all_cases) != 40:
        blockers.append(
            f"Expected 40 cases, found {len(all_cases)}."
        )

    for split, expected_count in (
        EXPECTED_SPLIT_COUNTS.items()
    ):
        actual_count = split_counts.get(split, 0)

        if actual_count != expected_count:
            blockers.append(
                f"Split `{split}` expected "
                f"{expected_count} cases, found "
                f"{actual_count}."
            )

    if review_counts.get("HUMAN_REVIEWED", 0) != len(
        all_cases
    ):
        blockers.append(
            "Not all evaluation cases are HUMAN_REVIEWED."
        )

    if missing_categories:
        blockers.append(
            "Missing evaluation categories: "
            + ", ".join(missing_categories)
        )

    if unused_documents:
        blockers.append(
            "Ground-truth documents without cases: "
            + ", ".join(unused_documents)
        )

    if evidence_leakage:
        blockers.append(
            f"Detected {len(evidence_leakage)} "
            "development/test evidence overlap(s)."
        )

    if duplicate_queries:
        blockers.append(
            f"Detected {len(duplicate_queries)} "
            "duplicate normalized query or queries."
        )

    if fact_similarity:
        warnings.append(
            f"Detected {len(fact_similarity)} "
            "cross-split fact-similarity candidate(s) "
            f"at threshold "
            f"{FACT_SIMILARITY_WARNING_THRESHOLD:.2f}."
        )

    unanswerable_count = answerability_counts.get(
        "UNANSWERABLE", 0
    )

    unanswerable_ratio = (
        unanswerable_count / len(all_cases)
        if all_cases
        else 0.0
    )

    if not 0.15 <= unanswerable_ratio <= 0.40:
        warnings.append(
            "UNANSWERABLE ratio is outside the "
            "recommended 15%–40% range."
        )

    closure_status = (
        "READY"
        if not blockers
        else "BLOCKED"
    )

    report_lines = [
        "# StudyBot Evaluation Dataset v1 Summary",
        "",
        f"**Closure status:** `{closure_status}`",
        "",
        "## Overview",
        "",
        markdown_table(
            ["Metric", "Value"],
            [
                ["Corpus entries", len(manifest)],
                [
                    "Ground-truth documents",
                    len(ground_truth_documents),
                ],
                ["Evaluation cases", len(all_cases)],
                [
                    "Human-reviewed cases",
                    review_counts.get(
                        "HUMAN_REVIEWED", 0
                    ),
                ],
                [
                    "Development cases",
                    split_counts.get(
                        "development", 0
                    ),
                ],
                [
                    "Test cases",
                    split_counts.get("test", 0),
                ],
                [
                    "Answerable cases",
                    answerability_counts.get(
                        "ANSWERABLE", 0
                    ),
                ],
                [
                    "Unanswerable cases",
                    unanswerable_count,
                ],
                [
                    "Unanswerable ratio",
                    f"{unanswerable_ratio:.1%}",
                ],
            ],
        ),
        "",
        "## Cases by document",
        "",
        markdown_table(
            ["Document ID", "Cases"],
            [
                [document_id, document_counts.get(
                    document_id, 0
                )]
                for document_id in sorted(
                    ground_truth_documents
                )
            ],
        ),
        "",
        "## Cases by category",
        "",
        markdown_table(
            ["Category", "Cases"],
            [
                [
                    category,
                    category_counts.get(category, 0),
                ]
                for category in sorted(
                    EXPECTED_CATEGORIES
                )
            ],
        ),
        "",
        "## Cases by query language",
        "",
        markdown_table(
            ["Language", "Cases"],
            [
                [language, count]
                for language, count in sorted(
                    language_counts.items()
                )
            ],
        ),
        "",
        "## Cases by answerability",
        "",
        markdown_table(
            ["Answerability", "Cases"],
            [
                [answerability, count]
                for answerability, count in sorted(
                    answerability_counts.items()
                )
            ],
        ),
        "",
        "## Closure blockers",
        "",
    ]

    if blockers:
        report_lines.extend(
            f"- {blocker}"
            for blocker in blockers
        )
    else:
        report_lines.append("- None.")

    report_lines.extend(
        [
            "",
            "## Warnings",
            "",
        ]
    )

    if warnings:
        report_lines.extend(
            f"- {warning}"
            for warning in warnings
        )
    else:
        report_lines.append("- None.")

    report_lines.extend(
        [
            "",
            "## Development/test evidence overlap",
            "",
        ]
    )

    if evidence_leakage:
        report_lines.append(
            markdown_table(
                [
                    "Document",
                    "Development case",
                    "Test case",
                    "Development locator",
                    "Test locator",
                ],
                [
                    [
                        finding["document_id"],
                        finding[
                            "development_case"
                        ],
                        finding["test_case"],
                        finding[
                            "development_locator"
                        ],
                        finding["test_locator"],
                    ]
                    for finding in evidence_leakage
                ],
            )
        )
    else:
        report_lines.append(
            "No evidence overlap detected."
        )

    report_lines.extend(
        [
            "",
            "## Cross-split fact-similarity candidates",
            "",
        ]
    )

    if fact_similarity:
        report_lines.append(
            markdown_table(
                [
                    "Development case",
                    "Test case",
                    "Shared documents",
                    "Jaccard similarity",
                ],
                [
                    [
                        finding[
                            "development_case"
                        ],
                        finding["test_case"],
                        finding[
                            "shared_documents"
                        ],
                        f"{finding['similarity']:.2f}",
                    ]
                    for finding in fact_similarity
                ],
            )
        )
    else:
        report_lines.append(
            "No high-similarity fact pairs detected."
        )

    report_lines.extend(
        [
            "",
            "## Duplicate queries",
            "",
        ]
    )

    if duplicate_queries:
        report_lines.extend(
            f"- {query}"
            for query in duplicate_queries
        )
    else:
        report_lines.append(
            "No duplicate normalized queries detected."
        )

    report_lines.extend(
        [
            "",
            "## Closure rule",
            "",
            "Dataset v1 can be marked complete only when:",
            "",
            "- All 40 cases are human-reviewed.",
            "- Split contains 30 development and 10 test cases.",
            "- All planned categories are represented.",
            "- Every ground-truth document has evaluation coverage.",
            "- No development/test evidence overlap remains.",
            "- No duplicate query remains.",
            "- Fact-similarity warnings have been manually reviewed.",
            "",
        ]
    )

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_PATH.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    print(
        f"Report written to: {REPORT_PATH}"
    )
    print(
        f"Closure status: {closure_status}"
    )

    if blockers:
        print("Blockers:")

        for blocker in blockers:
            print(f"- {blocker}")

        return 2

    if warnings:
        print("Warnings:")

        for warning in warnings:
            print(f"- {warning}")

    return 0


if __name__ == "__main__":
    sys.exit(main())