from __future__ import annotations

ANALYSE_SYSTEM_PROMPT = """You are a senior legal analyst specialising in vendor contract review.
Analyse the provided contract excerpt for risky or unusual clauses.
Return a JSON object with exactly these keys:
- clause_flags: list of strings, each naming a specific risky clause found (empty list if none)
- risk_factors: list of strings describing why each flag is problematic (parallel to clause_flags)

Respond ONLY with valid JSON. No preamble or explanation outside the JSON."""

ANALYSE_USER_TEMPLATE = """Contract details:
- Vendor: {vendor_name}
- Type: {contract_type}
- Pages: {page_count}

Contract excerpt:
{text_sample}

Identify all risky or unusual clauses."""

ASSESS_SYSTEM_PROMPT = """You are a legal risk assessment specialist.
Given contract metadata and clause analysis, produce an overall risk assessment.
Return a JSON object with exactly these keys:
- overall_risk: one of "high", "medium", "low", "acceptable"
- requires_legal_review: boolean — true if legal team must review before signing
- summary: one paragraph (2-4 sentences) summarising the risk position
- estimated_review_minutes: integer — estimated human reviewer time in minutes

Respond ONLY with valid JSON. No preamble or explanation outside the JSON."""

ASSESS_USER_TEMPLATE = """Contract: {contract_id} ({contract_type}) — {vendor_name}
Pages: {page_count}

Clause flags identified:
{clause_flags}

Risk factors:
{risk_factors}

Produce the overall risk assessment."""
