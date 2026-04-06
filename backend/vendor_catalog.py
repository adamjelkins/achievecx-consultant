"""
vendor_catalog.py

Vendor catalog and fit scoring engine for the CX AI Vendor Shortlist.

Scoring model (0-100):
  Flow Coverage      25pts  — how many confirmed flow categories vendor handles
  Volume Fit         20pts  — vendor typical deployment vs client volume
  Industry Fit       20pts  — vendor strength in client's industry
  Integration Match  20pts  — native connectors to client CRM/CC platform
  AI Capability      15pts  — vendor AI maturity vs client AI opportunity score

Monetization:
  featured: False         — flip to True when vendor relationship established
  featured_label: None    — set to "Partner" | "Sponsored" | "Featured"
  featured_boost: 5       — point boost applied to featured vendors (visible)

Top 3 vendors returned by default.
"""

try:
    import streamlit as st
except ImportError:
    import types, sys
    st = types.ModuleType('streamlit')
    st.session_state = types.SimpleNamespace()
    st.spinner = lambda x: __import__('contextlib').nullcontext()
    st.error = lambda x: None
    st.warning = lambda x: None
    st.info = lambda x: None
    sys.modules['streamlit'] = st


# --------------------------------------------------
# Vendor catalog
# --------------------------------------------------

VENDOR_CATALOG = [
    {
        "vendor_id":      "genesys",
        "name":           "Genesys",
        "tier":           "enterprise",
        "featured":       False,
        "featured_label": None,
        "featured_boost": 5,
        "description":    "Enterprise CCaaS platform with deep IVA, WEM, and AI capabilities. Strong in large, complex contact center environments.",
        "strengths":      [
            "Best-in-class IVA and conversational AI",
            "Comprehensive WFM / WFO suite",
            "Deep Salesforce and ServiceNow integrations",
            "Strong analytics and real-time dashboards",
        ],
        "best_for_industries": [
            "Retail", "Financial Services", "Insurance",
            "Healthcare", "Telecom", "Government",
        ],
        "flow_categories": [
            "self-service", "ivr", "agent-assist", "outbound",
            "authentication", "billing", "order-management",
        ],
        "volume_tiers":   ["high", "enterprise"],   # 10K+ contacts/month
        "integrations":   [
            "salesforce", "servicenow", "microsoft dynamics",
            "sap crm", "oracle cx",
        ],
        "website":        "https://www.genesys.com",
        "logo_domain":    "genesys.com",
    },
    {
        "vendor_id":      "nice_cxone",
        "name":           "NICE CXone",
        "tier":           "enterprise",
        "featured":       False,
        "featured_label": None,
        "featured_boost": 5,
        "description":    "Cloud-native CCaaS with strong AI, analytics, and quality management. Particularly strong in regulated industries.",
        "strengths":      [
            "Native AI with CXone Mpower platform",
            "Industry-leading quality management",
            "Strong compliance tooling (HIPAA, PCI)",
            "Unified desktop for agents",
        ],
        "best_for_industries": [
            "Healthcare", "Financial Services", "Insurance",
            "Retail", "Government", "Utilities",
        ],
        "flow_categories": [
            "self-service", "agent-assist", "quality-management",
            "authentication", "billing", "compliance",
        ],
        "volume_tiers":   ["high", "enterprise"],
        "integrations":   [
            "salesforce", "servicenow", "zendesk",
            "microsoft dynamics",
        ],
        "website":        "https://www.nice.com/cxone",
        "logo_domain":    "nice.com",
    },
    {
        "vendor_id":      "five9",
        "name":           "Five9",
        "tier":           "mid-market",
        "featured":       False,
        "featured_label": None,
        "featured_boost": 5,
        "description":    "Cloud contact center with strong AI automation and CRM integrations. Excellent mid-market option with fast deployment.",
        "strengths":      [
            "Fastest time-to-value in the industry",
            "Pre-built CRM connectors (Salesforce, HubSpot, Zendesk)",
            "Strong intelligent virtual agent capabilities",
            "Competitive pricing for mid-market",
        ],
        "best_for_industries": [
            "Retail", "Technology", "Financial Services",
            "Healthcare", "Professional Services",
        ],
        "flow_categories": [
            "self-service", "ivr", "agent-assist",
            "outbound", "order-management",
        ],
        "volume_tiers":   ["medium", "high"],   # 1K–50K contacts/month
        "integrations":   [
            "salesforce", "hubspot", "zendesk",
            "servicenow", "microsoft dynamics",
        ],
        "website":        "https://www.five9.com",
        "logo_domain":    "five9.com",
    },
    {
        "vendor_id":      "amazon_connect",
        "name":           "Amazon Connect",
        "tier":           "enterprise",
        "featured":       False,
        "featured_label": None,
        "featured_boost": 5,
        "description":    "AWS-native CCaaS with pay-per-use pricing and deep AI/ML integration via AWS services. Ideal for tech-forward organizations.",
        "strengths":      [
            "Consumption-based pricing — no per-seat cost",
            "Deep AWS AI/ML ecosystem (Lex, Comprehend, Polly)",
            "Unlimited scalability for volume spikes",
            "Strong API-first integration model",
        ],
        "best_for_industries": [
            "Technology", "Retail", "Financial Services",
            "Logistics", "Media",
        ],
        "flow_categories": [
            "self-service", "ivr", "authentication",
            "outbound", "order-management",
        ],
        "volume_tiers":   ["medium", "high", "enterprise"],
        "integrations":   [
            "salesforce", "servicenow", "zendesk",
            "hubspot",
        ],
        "website":        "https://aws.amazon.com/connect",
        "logo_domain":    "aws.amazon.com",
    },
    {
        "vendor_id":      "avaya",
        "name":           "Avaya",
        "tier":           "enterprise",
        "featured":       False,
        "featured_label": None,
        "featured_boost": 5,
        "description":    "Established enterprise communications platform with strong on-premise to cloud migration paths and deep telephony roots.",
        "strengths":      [
            "Strong migration path from on-premise PBX",
            "Deep enterprise telephony expertise",
            "Robust SLA and enterprise support",
            "Avaya Experience Platform AI capabilities",
        ],
        "best_for_industries": [
            "Government", "Healthcare", "Financial Services",
            "Manufacturing", "Utilities",
        ],
        "flow_categories": [
            "ivr", "agent-assist", "authentication",
            "compliance", "billing",
        ],
        "volume_tiers":   ["high", "enterprise"],
        "integrations":   [
            "salesforce", "servicenow", "microsoft dynamics",
        ],
        "website":        "https://www.avaya.com",
        "logo_domain":    "avaya.com",
    },
    {
        "vendor_id":      "twilio_flex",
        "name":           "Twilio Flex",
        "tier":           "mid-market",
        "featured":       False,
        "featured_label": None,
        "featured_boost": 5,
        "description":    "Fully programmable cloud contact center. Maximum flexibility for custom workflows and integrations. Developer-friendly.",
        "strengths":      [
            "Fully customizable — build exactly what you need",
            "Best-in-class APIs for custom integrations",
            "Strong omnichannel (SMS, WhatsApp, voice, chat)",
            "Competitive consumption-based pricing",
        ],
        "best_for_industries": [
            "Technology", "Retail", "Logistics",
            "Professional Services", "Media",
        ],
        "flow_categories": [
            "self-service", "outbound", "authentication",
            "order-management", "scheduling",
        ],
        "volume_tiers":   ["low", "medium", "high"],
        "integrations":   [
            "salesforce", "hubspot", "zendesk",
        ],
        "website":        "https://www.twilio.com/flex",
        "logo_domain":    "twilio.com",
    },
    {
        "vendor_id":      "cisco_webex",
        "name":           "Cisco Webex Contact Center",
        "tier":           "enterprise",
        "featured":       False,
        "featured_label": None,
        "featured_boost": 5,
        "description":    "Enterprise-grade cloud contact center tightly integrated with Webex collaboration suite. Strong for Cisco-infrastructure organizations.",
        "strengths":      [
            "Seamless Webex collaboration integration",
            "Strong for existing Cisco infrastructure",
            "AI-powered agent and customer experiences",
            "Robust security and compliance",
        ],
        "best_for_industries": [
            "Government", "Financial Services", "Healthcare",
            "Manufacturing", "Professional Services",
        ],
        "flow_categories": [
            "agent-assist", "ivr", "authentication",
            "billing", "compliance",
        ],
        "volume_tiers":   ["high", "enterprise"],
        "integrations":   [
            "salesforce", "servicenow", "microsoft dynamics",
        ],
        "website":        "https://www.webex.com/contact-center",
        "logo_domain":    "webex.com",
    },
    {
        "vendor_id":      "zendesk",
        "name":           "Zendesk",
        "tier":           "mid-market",
        "featured":       False,
        "featured_label": None,
        "featured_boost": 5,
        "description":    "Customer service platform with strong ticketing, AI, and omnichannel. Excellent for organizations with high email/chat volume.",
        "strengths":      [
            "Best-in-class ticketing and help desk",
            "Strong AI for ticket routing and resolution",
            "Excellent email and chat automation",
            "Large app marketplace for integrations",
        ],
        "best_for_industries": [
            "Technology", "Retail", "Professional Services",
            "Education", "Media",
        ],
        "flow_categories": [
            "self-service", "agent-assist", "order-management",
            "billing", "scheduling",
        ],
        "volume_tiers":   ["low", "medium", "high"],
        "integrations":   [
            "salesforce", "hubspot", "slack",
            "microsoft dynamics",
        ],
        "website":        "https://www.zendesk.com",
        "logo_domain":    "zendesk.com",
    },
    {
        "vendor_id":      "servicenow_csm",
        "name":           "ServiceNow CSM",
        "tier":           "enterprise",
        "featured":       False,
        "featured_label": None,
        "featured_boost": 5,
        "description":    "Enterprise service management with strong AI workflow automation. Ideal for complex B2B service environments.",
        "strengths":      [
            "Best workflow automation in enterprise service",
            "Deep B2B service management",
            "Strong AI for case routing and resolution",
            "Native ITSM integration for tech companies",
        ],
        "best_for_industries": [
            "Technology", "Financial Services", "Healthcare",
            "Manufacturing", "Government",
        ],
        "flow_categories": [
            "agent-assist", "self-service", "authentication",
            "compliance", "billing",
        ],
        "volume_tiers":   ["high", "enterprise"],
        "integrations":   [
            "salesforce", "genesys", "nice cxone",
            "microsoft dynamics",
        ],
        "website":        "https://www.servicenow.com/products/csm.html",
        "logo_domain":    "servicenow.com",
    },
    {
        "vendor_id":      "talkdesk",
        "name":           "Talkdesk",
        "tier":           "mid-market",
        "featured":       False,
        "featured_label": None,
        "featured_boost": 5,
        "description":    "AI-first cloud contact center with fast deployment and strong industry-specific solutions.",
        "strengths":      [
            "Strong AI-first architecture",
            "Industry clouds (retail, healthcare, financial)",
            "Fast deployment — 60-day go-live SLA",
            "Comprehensive agent productivity tools",
        ],
        "best_for_industries": [
            "Retail", "Healthcare", "Financial Services",
            "Technology", "Insurance",
        ],
        "flow_categories": [
            "self-service", "agent-assist", "outbound",
            "order-management", "billing",
        ],
        "volume_tiers":   ["medium", "high"],
        "integrations":   [
            "salesforce", "servicenow", "zendesk",
            "hubspot",
        ],
        "website":        "https://www.talkdesk.com",
        "logo_domain":    "talkdesk.com",
    },
    {
        "vendor_id":      "ujet",
        "name":           "UJET",
        "tier":           "mid-market",
        "featured":       False,
        "featured_label": None,
        "featured_boost": 5,
        "description":    "Mobile-first cloud contact center with unique smartphone integration and strong CRM-embedded approach.",
        "strengths":      [
            "Mobile-first customer experience",
            "CRM-embedded (native Salesforce/Zendesk)",
            "Strong for consumer-facing brands",
            "AI-powered deflection and routing",
        ],
        "best_for_industries": [
            "Retail", "Technology", "Financial Services",
            "Telecom", "Media",
        ],
        "flow_categories": [
            "self-service", "authentication", "order-management",
            "billing",
        ],
        "volume_tiers":   ["medium", "high"],
        "integrations":   [
            "salesforce", "zendesk", "hubspot",
        ],
        "website":        "https://ujet.cx",
        "logo_domain":    "ujet.cx",
    },
    {
        "vendor_id":      "kore_ai",
        "name":           "Kore.ai",
        "tier":           "specialist",
        "featured":       False,
        "featured_label": None,
        "featured_boost": 5,
        "description":    "Conversational AI specialist with deep virtual assistant and agent assist capabilities across voice and digital channels.",
        "strengths":      [
            "Best-in-class conversational AI platform",
            "Strong multilingual NLU",
            "Works with existing telephony (overlay approach)",
            "Deep agent assist and coaching capabilities",
        ],
        "best_for_industries": [
            "Financial Services", "Healthcare", "Retail",
            "Telecom", "Technology",
        ],
        "flow_categories": [
            "self-service", "agent-assist", "authentication",
            "billing", "scheduling",
        ],
        "volume_tiers":   ["medium", "high", "enterprise"],
        "integrations":   [
            "salesforce", "servicenow", "genesys",
            "nice cxone", "avaya",
        ],
        "website":        "https://kore.ai",
        "logo_domain":    "kore.ai",
    },
]


# --------------------------------------------------
# Volume tier mapping
# --------------------------------------------------

def _volume_tier(volume_str: str) -> str:
    """Map conversation answer to volume tier."""
    v = (volume_str or "").lower()
    if "50,000+" in v or "50000" in v:
        return "enterprise"
    elif "10,000" in v:
        return "high"
    elif "1,000" in v:
        return "medium"
    elif "under" in v:
        return "low"
    return "medium"


# --------------------------------------------------
# Fit scoring
# --------------------------------------------------

def _score_flow_coverage(vendor: dict, confirmed_flows: list,
                          assessment: dict) -> int:
    """
    25 pts — what fraction of confirmed flow categories does vendor cover?
    Uses flow categories from assessment scored_flows.
    """
    if not confirmed_flows:
        return 12  # neutral if no data

    vendor_cats = {c.lower() for c in vendor.get("flow_categories", [])}
    score_map   = {f["flow_id"]: f for f in assessment.get("scored_flows", [])}

    matched = 0
    for flow in confirmed_flows:
        fid      = flow["flow_id"]
        scored   = score_map.get(fid, {})
        category = (scored.get("category") or flow.get("category") or "").lower()
        flow_name = flow.get("flow_name", "").lower()

        # Direct category match
        if any(cat in category or cat in flow_name
               for cat in vendor_cats):
            matched += 1
        # Also check against vendor flow_categories keywords
        elif any(kw in flow_name for kw in vendor_cats):
            matched += 1

    ratio = matched / len(confirmed_flows)
    return round(ratio * 25)


def _score_volume_fit(vendor: dict, volume_str: str) -> int:
    """20 pts — does vendor's typical deployment match client volume?"""
    client_tier  = _volume_tier(volume_str)
    vendor_tiers = vendor.get("volume_tiers", [])

    if client_tier in vendor_tiers:
        return 20
    # Adjacent tiers get partial credit
    tier_order = ["low", "medium", "high", "enterprise"]
    try:
        c_idx = tier_order.index(client_tier)
        for tier in vendor_tiers:
            if tier in tier_order:
                v_idx = tier_order.index(tier)
                if abs(c_idx - v_idx) == 1:
                    return 12
    except ValueError:
        pass
    return 5


def _score_industry_fit(vendor: dict, industry: str) -> int:
    """20 pts — is vendor strong in client's industry?"""
    vendor_industries = [i.lower() for i in vendor.get("best_for_industries", [])]
    client_industry   = (industry or "").lower()

    if not client_industry or client_industry == "unknown":
        return 10  # neutral

    # Exact match
    if client_industry in vendor_industries:
        return 20

    # Partial match (e.g. "financial" matches "financial services")
    for vi in vendor_industries:
        if client_industry in vi or vi in client_industry:
            return 15

    return 5


def _score_integration_match(vendor: dict, crm: str, cc_platform: str) -> int:
    """20 pts — does vendor have native connectors to client's platforms?"""
    vendor_integrations = [i.lower() for i in vendor.get("integrations", [])]
    points = 0

    if crm:
        crm_lower = crm.lower()
        if any(crm_lower in vi or vi in crm_lower
               for vi in vendor_integrations):
            points += 12

    if cc_platform:
        cc_lower = cc_platform.lower()
        # Check if this vendor IS the CC platform
        if cc_lower in vendor["vendor_id"].lower() or \
           vendor["name"].lower() in cc_lower:
            points += 8
        elif any(cc_lower in vi or vi in cc_lower
                 for vi in vendor_integrations):
            points += 8

    # If no data, return neutral
    if not crm and not cc_platform:
        return 10

    return min(points, 20)


def _score_ai_capability(vendor: dict, ai_score: int) -> int:
    """
    15 pts — does vendor's AI maturity align with client's AI opportunity?
    High AI score clients need a vendor with deep AI capabilities.
    """
    tier = vendor.get("tier", "mid-market")

    # Enterprise and specialist vendors have deepest AI
    vendor_ai_strength = {
        "enterprise":  85,
        "mid-market":  65,
        "specialist":  90,   # specialists (Kore.ai) have deepest AI
    }.get(tier, 65)

    # Reward alignment — penalize mismatch in either direction
    delta = abs(ai_score - vendor_ai_strength)
    if delta <= 10:
        return 15
    elif delta <= 25:
        return 10
    elif delta <= 40:
        return 6
    return 3


# --------------------------------------------------
# Why-this-fits explanation
# --------------------------------------------------

def _build_fit_reasons(
    vendor: dict,
    confirmed_flows: list,
    industry: str,
    crm: str,
    cc_platform: str,
    volume_str: str,
    ai_score: int,
    assessment: dict,
) -> list[str]:
    """Build 3-4 specific reasons this vendor fits the client."""
    reasons = []

    # Flow coverage
    score_map = {f["flow_id"]: f for f in assessment.get("scored_flows", [])}
    vendor_cats = {c.lower() for c in vendor.get("flow_categories", [])}
    covered = []
    for flow in confirmed_flows[:6]:
        fname = flow.get("flow_name", "").lower()
        cat   = (score_map.get(flow["flow_id"], {}).get("category") or
                 flow.get("category") or "").lower()
        if any(kw in fname or kw in cat for kw in vendor_cats):
            covered.append(flow.get("flow_name", ""))
    if covered:
        reasons.append(
            f"Covers {len(covered)} of your confirmed flows including "
            f"{', '.join(covered[:2])}"
            + (" and more" if len(covered) > 2 else "")
        )

    # Industry fit
    vendor_industries = [i.lower() for i in vendor.get("best_for_industries", [])]
    if industry and industry.lower() in vendor_industries:
        reasons.append(f"Strong track record in {industry}")

    # Integration
    vendor_integrations = [i.lower() for i in vendor.get("integrations", [])]
    if crm and any(crm.lower() in vi or vi in crm.lower()
                   for vi in vendor_integrations):
        reasons.append(f"Native {crm} integration available")
    if cc_platform and vendor["name"].lower() in cc_platform.lower():
        reasons.append(f"Your existing {cc_platform} platform")

    # Volume
    client_tier  = _volume_tier(volume_str)
    vendor_tiers = vendor.get("volume_tiers", [])
    if client_tier in vendor_tiers:
        reasons.append(
            f"Optimized for {client_tier.replace('enterprise', 'large enterprise')} "
            f"contact volumes"
        )

    # AI capability
    if ai_score >= 70 and vendor.get("tier") in ("enterprise", "specialist"):
        reasons.append("Advanced AI capabilities match your high opportunity score")
    elif ai_score < 40 and vendor.get("tier") == "mid-market":
        reasons.append("Practical AI features appropriate for your current maturity")

    # Always include a strength
    strengths = vendor.get("strengths", [])
    if strengths and len(reasons) < 4:
        reasons.append(strengths[0])

    return reasons[:4]


# --------------------------------------------------
# Main scoring function
# --------------------------------------------------

def score_vendors(
    confirmed_flows: list,
    industry: str,
    crm: str,
    cc_platform: str,
    volume_str: str,
    ai_score: int,
    assessment: dict,
    top_n: int = 3,
) -> list[dict]:
    """
    Score all vendors and return top N.
    Featured vendors get a transparent boost (+featured_boost points).
    Returns list of vendor dicts with scores added.
    """
    scored = []

    for vendor in VENDOR_CATALOG:
        flow_pts  = _score_flow_coverage(vendor, confirmed_flows, assessment)
        vol_pts   = _score_volume_fit(vendor, volume_str)
        ind_pts   = _score_industry_fit(vendor, industry)
        int_pts   = _score_integration_match(vendor, crm, cc_platform)
        ai_pts    = _score_ai_capability(vendor, ai_score)

        base_score = flow_pts + vol_pts + ind_pts + int_pts + ai_pts

        # Featured boost — transparent, shown in UI
        featured_boost = vendor["featured_boost"] if vendor["featured"] else 0
        total_score    = min(base_score + featured_boost, 100)

        fit_reasons = _build_fit_reasons(
            vendor, confirmed_flows, industry, crm, cc_platform,
            volume_str, ai_score, assessment,
        )

        scored.append({
            **vendor,
            "fit_score":        total_score,
            "base_score":       base_score,
            "featured_boost":   featured_boost,
            "score_breakdown": {
                "Flow Coverage":     flow_pts,
                "Volume Fit":        vol_pts,
                "Industry Fit":      ind_pts,
                "Integration Match": int_pts,
                "AI Capability":     ai_pts,
            },
            "fit_reasons": fit_reasons,
            "flows_covered": sum(
                1 for f in confirmed_flows
                if any(
                    kw in f.get("flow_name","").lower()
                    for kw in {c.lower() for c in vendor["flow_categories"]}
                )
            ),
        })

    # Sort: featured vendors with same score go first, then by fit_score
    scored.sort(
        key=lambda v: (v["fit_score"], v["featured"]),
        reverse=True,
    )

    return scored[:top_n]


# --------------------------------------------------
# Session state entry point
# --------------------------------------------------

def run_vendor_shortlist() -> list[dict]:
    """
    Run vendor scoring from session state.
    Caches result in st.session_state.vendor_shortlist.
    """
    answers    = st.session_state.get("conv_answers", {})
    bp         = st.session_state.get("business_profile", {})
    assessment = st.session_state.get("assessment", {})
    discovery  = st.session_state.get("discovery", [])

    confirmed_flows = [f for f in discovery if f.get("confirmed")]
    industry        = bp.get("industry", "")
    crm             = answers.get("crm", "") or ""
    cc_platform     = answers.get("cc_platform", "") or ""
    volume_str      = answers.get("volume", "") or ""
    ai_score        = assessment.get("business_ai_score", 50)

    results = score_vendors(
        confirmed_flows = confirmed_flows,
        industry        = industry,
        crm             = crm,
        cc_platform     = cc_platform,
        volume_str      = volume_str,
        ai_score        = ai_score,
        assessment      = assessment,
        top_n           = 3,
    )

    st.session_state.vendor_shortlist = results
    return results


def get_or_run_vendor_shortlist() -> list[dict]:
    """Return cached shortlist or run fresh."""
    existing  = st.session_state.get("vendor_shortlist")
    discovery = st.session_state.get("discovery", [])
    confirmed_ids = sorted(
        f["flow_id"] for f in discovery if f.get("confirmed")
    )

    if existing:
        # Invalidate if confirmed flows changed since last run
        last_ids = st.session_state.get("vendor_shortlist_flow_ids", [])
        if last_ids == confirmed_ids:
            return existing

    results = run_vendor_shortlist()
    st.session_state.vendor_shortlist_flow_ids = confirmed_ids
    return results