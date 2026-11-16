from app.agents.supervisor import extract_evidence
from app.services.observability.usage_logger import estimate_gemini_cost


def test_evidence_extraction():
    sample_text = (
        "Investigation indicates that issue PAY-142 is blocked by PAY-139. "
        "Additionally, PR #204 is waiting for code review and PR 211 failed CI."
    )
    evidence = extract_evidence(sample_text)
    keys = [e.key for e in evidence]
    assert "PAY-142" in keys
    assert "PAY-139" in keys
    assert "PR #204" in keys
    assert "PR #211" in keys


def test_gemini_cost_estimation():
    cost = estimate_gemini_cost(10_000, 1_000)
    assert cost > 0
    # 10k input = 0.00075, 1k output = 0.00030 -> 0.00105
    assert 0.001 <= cost <= 0.0011
