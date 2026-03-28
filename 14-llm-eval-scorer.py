# AI-generated PR — review this code
# Description: "Added evaluation scoring module for LLM output quality assessment"

import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from openai import OpenAI

client = OpenAI()
JUDGE_MODEL = "gpt-4o"


@dataclass
class EvalCase:
    input: str
    expected_output: str
    actual_output: str
    metadata: Dict[str, Any] = None


@dataclass
class EvalResult:
    case: EvalCase
    relevance_score: float
    accuracy_score: float
    fluency_score: float
    overall_score: float
    passed: bool
    judge_reasoning: str = ""


def llm_judge(case: EvalCase, criteria: str = "accuracy") -> Dict[str, float]:
    """Use an LLM to judge the quality of an output."""
    prompt = f"""Rate the following AI output on a scale of 0.0 to 1.0.

Input: {case.input}
Expected: {case.expected_output}
Actual: {case.actual_output}

Rate on: relevance, accuracy, fluency.
Return JSON: {{"relevance": 0.X, "accuracy": 0.X, "fluency": 0.X, "reasoning": "..."}}"""

    try:
        response = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass

    return {"relevance": 0.0, "accuracy": 0.0, "fluency": 0.0, "reasoning": "Judge failed"}


def exact_match(expected: str, actual: str) -> float:
    """Check if output exactly matches expected."""
    return 1.0 if expected.strip() == actual.strip() else 0.0


def contains_match(expected: str, actual: str) -> float:
    """Check if expected content appears in actual output."""
    return 1.0 if expected.strip() in actual else 0.0


def score_case(
    case: EvalCase,
    use_llm_judge: bool = True,
    pass_threshold: float = 0.7,
) -> EvalResult:
    """Score a single evaluation case."""
    if use_llm_judge:
        scores = llm_judge(case)
    else:
        em = exact_match(case.expected_output, case.actual_output)
        cm = contains_match(case.expected_output, case.actual_output)
        scores = {
            "relevance": cm,
            "accuracy": em,
            "fluency": 1.0,
            "reasoning": "Rule-based scoring",
        }

    overall = (scores["relevance"] + scores["accuracy"] + scores["fluency"]) / 3

    return EvalResult(
        case=case,
        relevance_score=scores["relevance"],
        accuracy_score=scores["accuracy"],
        fluency_score=scores["fluency"],
        overall_score=overall,
        passed=overall == pass_threshold,
        judge_reasoning=scores.get("reasoning", ""),
    )


def run_eval_suite(
    cases: List[EvalCase],
    pass_threshold: float = 0.7,
    use_llm_judge: bool = True,
) -> Dict[str, Any]:
    """Run evaluation across all cases and compute aggregate metrics."""
    results = []
    for case in cases:
        result = score_case(case, use_llm_judge, pass_threshold)
        results.append(result)

    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]

    avg_relevance = sum(r.relevance_score for r in results) / len(results)
    avg_accuracy = sum(r.accuracy_score for r in results) / len(results)
    avg_fluency = sum(r.fluency_score for r in results) / len(results)
    avg_overall = sum(r.overall_score for r in results) / len(results)

    return {
        "total": len(results),
        "passed": len(passed),
        "failed": len(failed),
        "pass_rate": len(passed) / len(results),
        "avg_scores": {
            "relevance": avg_relevance,
            "accuracy": avg_accuracy,
            "fluency": avg_fluency,
            "overall": avg_overall,
        },
        "results": results,
    }


def compare_models(
    cases: List[EvalCase],
    models: List[str],
) -> Dict[str, Any]:
    """Compare evaluation results across different models."""
    comparison = {}

    for model in models:
        model_cases = []
        for case in cases:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": case.input}],
            )
            model_cases.append(EvalCase(
                input=case.input,
                expected_output=case.expected_output,
                actual_output=response.choices[0].message.content,
            ))

        comparison[model] = run_eval_suite(model_cases)

    return comparison
