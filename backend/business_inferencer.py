"""
business_inferencer.py

Two-step GPT inference pipeline triggered after intake.

Step 1 — Business Research:
    Uses the email domain to infer company name, industry,
    company type, and size using GPT's training knowledge.
    No web search tool required — works with all OpenAI SDK versions.

Step 2 — CX Flow Pre-suggestion:
    Uses the inferred business profile to pre-suggest canonical
    flows from flows.json before the user types anything.

Both calls are stateless — take inputs, return structured dicts.
Callers are responsible for persisting to session state.
"""

import json
import os
from datetime import datetime
from pathlib import Path

import openai
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

FLOWS_FILE = os.path.join(Path.cwd(), "data", "flows.json")
INFERENCE_MODEL = "gpt-4o-mini"


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _load_flows() -> list:
    try:
        with open(FLOWS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _extract_domain(email: str) -> str:
    """Extract domain from email address."""
    try:
        return email.strip().split("@")[1].lower()
    except IndexError:
        return ""


def _call_gpt(messages: list, max_tokens: int = 800) -> str:
    """
    Call GPT chat completion (no tools — works with all SDK versions).
    Returns the text content of the response.
    """
    response = client.chat.completions.create(
        model=INFERENCE_MODEL,
        messages=messages,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content or ""
    return content.strip()


def _safe_parse_json(raw: str) -> dict | list:
    """
    Attempt to parse JSON from GPT response.
    Strips markdown code fences if present.
    Returns dict or list depending on content.
    """
    cleaned = raw.strip()

    # Strip ```json ... ``` or ``` ... ``` fences
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()

    # Find the first { or [ and parse from there
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = cleaned.find(start_char)
        end = cleaned.rfind(end_char)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except Exception:
                continue

    return {}


# --------------------------------------------------
# Step 1 — Business Research
# --------------------------------------------------

def infer_business_from_domain(domain: str) -> dict:
    """
    Use GPT knowledge to infer business details from email domain.

    Returns:
        {
            "domain": str,
            "company_name": str,
            "industry": str,
            "company_type": str,
            "size_estimate": str,
            "description": str,
            "confidence": float,
            "source": "gpt_inferred",
            "inferred_at": str,
        }
    """
    if not domain:
        return _empty_business_profile(domain)

    prompt = f"""You are a business intelligence assistant with broad knowledge of companies.

A user has signed up with the email domain: {domain}

Based on your knowledge of this domain/company, provide business details.
If you recognize this domain, use what you know. If not, make a reasonable inference
from the domain name itself (e.g. "retailco.com" suggests a retail company).

Return ONLY a valid JSON object — no markdown, no explanation, just JSON:
{{
  "company_name": "the company or organization name",
  "industry": "primary industry — choose one of: Retail, Healthcare, Financial Services, Telecom, Insurance, Technology, Hospitality, Logistics, Education, Government, Manufacturing, Professional Services, Other",
  "company_type": "short description of what they do, e.g. Regional retail chain, SaaS software company, Community bank",
  "size_estimate": "one of: SMB, Mid-market, Enterprise",
  "description": "one sentence describing the business",
  "confidence": 0.85
}}

Set confidence between 0.3 (domain unknown, pure guess) and 0.95 (well-known company).
Return ONLY the JSON object."""

    try:
        raw = _call_gpt(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        parsed = _safe_parse_json(raw)

        if not isinstance(parsed, dict) or not parsed.get("company_name"):
            raise ValueError("Empty or invalid response")

        return {
            "domain": domain,
            "company_name": parsed.get("company_name", domain),
            "industry": parsed.get("industry", "Unknown"),
            "company_type": parsed.get("company_type", ""),
            "size_estimate": parsed.get("size_estimate", "Unknown"),
            "description": parsed.get("description", ""),
            "confidence": min(float(parsed.get("confidence", 0.5)), 1.0),
            "source": "gpt_inferred",
            "inferred_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        print(f"[inferencer] Business research failed for {domain}: {e}")
        return _empty_business_profile(domain)


def _empty_business_profile(domain: str) -> dict:
    return {
        "domain": domain,
        "company_name": domain,
        "industry": "Unknown",
        "company_type": "",
        "size_estimate": "Unknown",
        "description": "",
        "confidence": 0.0,
        "source": "fallback",
        "inferred_at": datetime.utcnow().isoformat(),
    }


# --------------------------------------------------
# Step 2 — CX Flow Pre-suggestion
# --------------------------------------------------

def suggest_flows_from_profile(business_profile: dict) -> list:
    """
    Use the inferred business profile to pre-suggest canonical CX flows.

    Returns a list of dicts:
        [
            {
                "flow_id": "flow_012",
                "flow_name": "Order Inquiry",
                "confidence": 0.85,
                "reason": "Common for retail businesses",
                "source": "gpt_inferred",
            },
            ...
        ]
    """
    flows = _load_flows()
    if not flows:
        return []

    # Build compact flow catalog for prompt
    flow_catalog = [
        {
            "flow_id": f["flow_id"],
            "flow_name": f["flow_name"],
            "category": f.get("category", ""),
            "keywords": f.get("keywords", []),
        }
        for f in flows
    ]

    company_name = business_profile.get("company_name", "this company")
    industry = business_profile.get("industry", "Unknown")
    company_type = business_profile.get("company_type", "")
    size = business_profile.get("size_estimate", "Unknown")
    description = business_profile.get("description", "")

    prompt = f"""You are a CX architecture expert.

Business context:
- Company: {company_name}
- Industry: {industry}
- Type: {company_type}
- Size: {size}
- Description: {description}

Available CX interaction flows:
{json.dumps(flow_catalog, indent=2)}

Based on the business context, select the most likely customer interaction flows
this company would need. Order them from most to least likely.

Return ONLY a valid JSON array — no markdown, no explanation:
[
  {{
    "flow_id": "flow_012",
    "flow_name": "Order Inquiry",
    "confidence": 0.90,
    "reason": "Retail businesses receive high volumes of order status inquiries"
  }}
]

Include 4 to 8 flows. Only include flows with confidence >= 0.40.
Use exact flow_id values from the catalog above.
Return ONLY the JSON array."""

    try:
        raw = _call_gpt(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
        )
        parsed = _safe_parse_json(raw)

        # parsed may be a list directly or wrapped in a dict
        if isinstance(parsed, list):
            suggestions = parsed
        elif isinstance(parsed, dict):
            suggestions = (
                parsed.get("flows")
                or parsed.get("suggestions")
                or parsed.get("results")
                or []
            )
        else:
            suggestions = []

        # Validate against known flow_ids, log unmatched ones
        known_ids = {f["flow_id"] for f in flows}
        result    = []
        unmapped  = []

        for s in suggestions:
            if not isinstance(s, dict):
                continue
            fid = s.get("flow_id", "")
            if fid not in known_ids:
                # GPT suggested something we don't have — log it
                name = s.get("flow_name", fid)
                if name and name not in known_ids:
                    unmapped.append(name)
                continue
            result.append({
                "flow_id":    fid,
                "flow_name":  s.get("flow_name", fid),
                "confidence": min(float(s.get("confidence", 0.5)), 1.0),
                "reason":     s.get("reason", ""),
                "source":     "gpt_inferred",
            })

        # Log unmapped suggestions to data/unmapped_flows.json
        if unmapped:
            try:
                from streamlit_app.flows import log_unmapped_suggestions
                log_unmapped_suggestions(unmapped)
            except Exception as e:
                print(f"[inferencer] Failed to log unmapped suggestions: {e}")

        return result

    except Exception as e:
        print(f"[inferencer] Flow suggestion failed: {e}")
        return []


# --------------------------------------------------
# Combined Entry Point
# --------------------------------------------------

def run_full_inference(email: str) -> dict:
    """
    Runs both inference steps and returns the complete business_profile dict
    ready to be stored in st.session_state.business_profile and leads.json.
    """
    domain = _extract_domain(email)

    # Step 1 — business research
    business_profile = infer_business_from_domain(domain)

    # Step 2 — flow pre-suggestion
    pre_suggested_flows = suggest_flows_from_profile(business_profile)

    business_profile["pre_suggested_flows"] = pre_suggested_flows
    business_profile["inference_complete"] = True

    return business_profile