from app.models import EvidenceItem

EXPERT_SHARED_CONTRACT = """\
Return only structured data matching ExpertAssessment.
Rules:
- Do not produce a final product score or final verdict.
- Do not add URLs or new external sources.
- Cite evidence only by evidence_id.
- Every reason must either cite valid evidence IDs or be marked as based on input_text.
- Preserve uncertainty and state missing information.
- Use cautious wording such as "nguy cơ", "dấu hiệu", "chưa đủ bằng chứng".
"""

ROLE_CONTRACTS: dict[str, str] = {
    "financial": """\
Question: Does the message use financial mechanisms commonly associated with fraud?
Focus:
- Transfer destination.
- Upfront fees.
- Guaranteed return.
- Payment urgency.
- Unusual payment rails.
- Mismatch between claim and payment request.
""",
    "legal_risk": """\
Question: Does the claim misuse legal or official authority, or conflict with
common official procedures?
Boundaries:
- This is not legal advice.
- Do not assert illegality without evidence.
- Highlight procedure inconsistencies.
- Recommend independent verification through official channels.
""",
    "cyber": """\
Question: Are there phishing, credential theft, malicious-link or account-takeover signals?
Focus:
- Domain mismatch.
- Suspicious link structure.
- Credential request.
- OTP request.
- Remote access.
- Device installation request.
- Security urgency.
""",
    "osint": """\
Question: What do the provided evidence items say about entities, domains, phone numbers and claims?
Focus:
- Official advisories.
- Repeated reports.
- Cross-source corroboration.
- Source reliability.
- Missing evidence.
OSINT may cite only provided evidence IDs.
""",
}

REPAIR_PROMPT_INSTRUCTION = """\
Your previous structured output was invalid.
Repair it once:
- Match the ExpertAssessment schema exactly.
- Remove URLs and unsupported external claims.
- Use only the provided evidence IDs.
- If a reason has no valid evidence ID, mark it as input_text.
"""


def build_expert_prompt(role: object, text: str, evidence: list[EvidenceItem]) -> str:
    role_value = getattr(role, "value", str(role))
    return (
        f"{EXPERT_SHARED_CONTRACT}\n"
        f"Role: {role_value}\n"
        f"{ROLE_CONTRACTS[role_value]}\n"
        f"User text:\n{text}\n\n"
        f"Evidence items available for citation:\n{_format_evidence(evidence)}"
    )


def build_expert_repair_prompt(original_prompt: str) -> str:
    return f"{original_prompt}\n\n{REPAIR_PROMPT_INSTRUCTION}"


def _format_evidence(evidence: list[EvidenceItem]) -> str:
    if not evidence:
        return "No external evidence was provided. Base reasons on input_text only."

    lines: list[str] = []
    for item in evidence:
        lines.append(
            "\n".join(
                [
                    f"- evidence_id: {item.evidence_id}",
                    f"  title: {item.title}",
                    f"  source_name: {item.source_name}",
                    f"  published_at: {item.published_at or 'not available'}",
                    f"  snippet: {item.snippet}",
                    f"  credibility_score: {item.credibility_score}",
                    f"  relevance_score: {item.relevance_score}",
                ]
            )
        )
    return "\n".join(lines)
