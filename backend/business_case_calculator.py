"""
business_case_calculator.py

Pure Python formula engine for the CX Business Case Calculator.
No Streamlit dependencies — all inputs/outputs are plain dicts.

Runs three scenarios: conservative, base, optimistic.
Based on the TCO/ROI model from the reference spreadsheet.
"""

import math
from dataclasses import dataclass, field
from typing import Literal


# --------------------------------------------------
# Scenario multipliers
# --------------------------------------------------

SCENARIO_MULTIPLIERS = {
    "conservative": {
        "automation_pct_factor":    0.80,   # achieve 80% of target automation
        "churn_reduction_factor":   0.60,   # 60% of projected churn improvement
        "impl_cost_factor":         1.20,   # implementation costs 20% more
        "auto_contact_cost_factor": 1.15,   # automation costs 15% more per contact
        "savings_haircut":          0.82,   # apply 18% haircut to total savings
        "label":                    "Conservative",
        "color":                    "#f59e0b",
        "description":              "Slower adoption, modest churn improvement, some implementation overrun.",
    },
    "base": {
        "automation_pct_factor":    1.00,
        "churn_reduction_factor":   1.00,
        "impl_cost_factor":         1.00,
        "auto_contact_cost_factor": 1.00,
        "savings_haircut":          1.00,
        "label":                    "Base Case",
        "color":                    "#818cf8",
        "description":              "Typical deployment based on industry benchmarks.",
    },
    "optimistic": {
        "automation_pct_factor":    1.20,   # achieve 120% of target (capped at 80% max)
        "churn_reduction_factor":   1.40,   # 40% better churn improvement than expected
        "impl_cost_factor":         0.85,   # comes in 15% under budget
        "auto_contact_cost_factor": 0.88,   # automation costs less per contact
        "savings_haircut":          1.18,   # 18% upside on total savings
        "label":                    "Optimistic",
        "color":                    "#22c55e",
        "description":              "Fast adoption, strong churn outcomes, implementation under budget.",
    },
}


# --------------------------------------------------
# Input dataclass
# --------------------------------------------------

@dataclass
class BusinessCaseInputs:
    # Contact volume
    annual_contacts:        int     = 25_000
    voice_pct:              float   = 0.60
    chat_pct:               float   = 0.40
    email_pct:              float   = 0.00
    current_automation_pct: float   = 0.00   # existing self-service

    # Staffing — current
    agent_count:            int     = 100
    hourly_agent_cost:      float   = 17.00
    burden_rate:            float   = 0.18
    churn_rate:             float   = 0.32
    ramp_days:              int     = 90
    extended_ramp_days:     int     = 60
    recruitment_cost:       float   = 4_000.00
    wfm_fte_count:          int     = 2
    wfm_fte_salary:         float   = 55_000.00
    qa_fte_count:           int     = 1
    qa_fte_salary:          float   = 55_000.00

    # Technology — current
    ccaas_cost_per_agent_month: float = 100.00
    other_tech_annual:          float = 0.00

    # Proposed state
    target_automation_pct:      float = 0.40
    proposed_churn_rate:        float = 0.21
    proposed_ramp_days:         int   = 60
    proposed_extended_ramp_days:int   = 30
    proposed_recruitment_cost:  float = 2_000.00
    proposed_wfm_fte_count:     int   = 1
    proposed_qa_fte_count:      int   = 1
    cost_per_automated_contact: float = 0.50
    proposed_ccaas_per_agent_month: float = 150.00

    # Automation tech add-ons (monthly per agent)
    wfm_wfo_addon:          float = 40.00
    auto_qa_addon:          float = 40.00
    sim_training_addon:     float = 30.00
    ai_agent_assist_addon:  float = 40.00

    # Implementation
    implementation_cost:    float = 1_000_000.00

    # Analysis horizon
    analysis_years:         int   = 5

    # Contacts per agent per day (industry standard)
    contacts_per_agent_per_day: float = 38.46
    work_days_per_year:         int   = 260


# --------------------------------------------------
# Environment cost model
# --------------------------------------------------

def _calc_environment(
    annual_contacts:        int,
    current_automation_pct: float,
    agent_count:            int,
    hourly_agent_cost:      float,
    burden_rate:            float,
    churn_rate:             float,
    ramp_days:              int,
    extended_ramp_days:     int,
    recruitment_cost:       float,
    wfm_fte_count:          int,
    wfm_fte_salary:         float,
    qa_fte_count:           int,
    qa_fte_salary:          float,
    ccaas_cost_per_agent_month: float,
    other_tech_annual:      float,
    contacts_per_agent_per_day: float,
    work_days_per_year:     int,
    # Automation costs (proposed environment only)
    automated_contacts:     int   = 0,
    cost_per_automated_contact: float = 0.0,
    wfm_wfo_addon:          float = 0.0,
    auto_qa_addon:          float = 0.0,
    sim_training_addon:     float = 0.0,
    ai_agent_assist_addon:  float = 0.0,
) -> dict:
    """Calculate full cost model for one environment."""

    human_contacts  = annual_contacts * (1 - current_automation_pct)
    self_service    = annual_contacts * current_automation_pct

    # Annual agent cost
    annual_hours    = work_days_per_year * 8
    loaded_annual   = hourly_agent_cost * annual_hours * (1 + burden_rate)
    labor_cost      = agent_count * loaded_annual

    # Churn cost
    churned_agents   = agent_count * churn_rate
    hourly_daily     = hourly_agent_cost * 8
    ramp_loss        = churned_agents * ramp_days * hourly_daily
    # Extended ramp: agents at ~50% proficiency during extended ramp
    ext_ramp_loss    = (
        churned_agents
        * (extended_ramp_days / work_days_per_year)
        * loaded_annual
        * 0.50
    )
    recruiting_cost  = churned_agents * recruitment_cost
    churn_cost       = ramp_loss + ext_ramp_loss + recruiting_cost

    # Tech stack
    ccaas_annual     = ccaas_cost_per_agent_month * agent_count * 12
    addon_per_agent_month = (
        wfm_wfo_addon + auto_qa_addon + sim_training_addon + ai_agent_assist_addon
    )
    addon_annual     = addon_per_agent_month * agent_count * 12
    automation_cost  = automated_contacts * cost_per_automated_contact
    tech_cost        = ccaas_annual + addon_annual + automation_cost + other_tech_annual

    # WFM / QA overhead
    wfm_cost         = wfm_fte_count * wfm_fte_salary * (1 + burden_rate)
    qa_cost          = qa_fte_count  * qa_fte_salary  * (1 + burden_rate)
    overhead_cost    = wfm_cost + qa_cost

    total_cost       = labor_cost + churn_cost + tech_cost + overhead_cost
    cpc              = total_cost / annual_contacts if annual_contacts > 0 else 0

    return {
        "annual_contacts":   annual_contacts,
        "human_contacts":    int(human_contacts),
        "self_service":      int(self_service),
        "agent_count":       agent_count,
        "labor_cost":        labor_cost,
        "churn_cost":        churn_cost,
        "churned_agents":    churned_agents,
        "ramp_loss":         ramp_loss,
        "ext_ramp_loss":     ext_ramp_loss,
        "recruiting_cost":   recruiting_cost,
        "tech_cost":         tech_cost,
        "ccaas_annual":      ccaas_annual,
        "addon_annual":      addon_annual,
        "automation_cost":   automation_cost,
        "overhead_cost":     overhead_cost,
        "wfm_cost":          wfm_cost,
        "qa_cost":           qa_cost,
        "total_cost":        total_cost,
        "cost_per_contact":  cpc,
        "loaded_annual_per_agent": loaded_annual,
    }


# --------------------------------------------------
# Scenario runner
# --------------------------------------------------

def _run_scenario(
    inputs: BusinessCaseInputs,
    scenario: str,
) -> dict:
    """Run the full model for one scenario."""
    m = SCENARIO_MULTIPLIERS[scenario]

    # ── Current environment ──
    current = _calc_environment(
        annual_contacts         = inputs.annual_contacts,
        current_automation_pct  = inputs.current_automation_pct,
        agent_count             = inputs.agent_count,
        hourly_agent_cost       = inputs.hourly_agent_cost,
        burden_rate             = inputs.burden_rate,
        churn_rate              = inputs.churn_rate,
        ramp_days               = inputs.ramp_days,
        extended_ramp_days      = inputs.extended_ramp_days,
        recruitment_cost        = inputs.recruitment_cost,
        wfm_fte_count           = inputs.wfm_fte_count,
        wfm_fte_salary          = inputs.wfm_fte_salary,
        qa_fte_count            = inputs.qa_fte_count,
        qa_fte_salary           = inputs.qa_fte_salary,
        ccaas_cost_per_agent_month = inputs.ccaas_cost_per_agent_month,
        other_tech_annual       = inputs.other_tech_annual,
        contacts_per_agent_per_day = inputs.contacts_per_agent_per_day,
        work_days_per_year      = inputs.work_days_per_year,
    )

    # ── Proposed environment ──
    # Apply scenario factor to target automation, cap at 80%
    effective_automation = min(
        inputs.target_automation_pct * m["automation_pct_factor"],
        0.80,
    )
    automated_contacts  = int(inputs.annual_contacts * effective_automation)
    remaining_contacts  = inputs.annual_contacts - automated_contacts

    # Derive new agent count from remaining volume
    proposed_agent_count = max(
        math.ceil(
            remaining_contacts
            / inputs.contacts_per_agent_per_day
            / inputs.work_days_per_year
        ),
        1,
    )

    # Churn improvement: blend factor with scenario
    churn_improvement   = (inputs.churn_rate - inputs.proposed_churn_rate)
    effective_churn_reduction = churn_improvement * m["churn_reduction_factor"]
    proposed_churn_rate = max(
        inputs.churn_rate - effective_churn_reduction,
        0.05,  # floor at 5%
    )

    # Ramp improvements (fixed regardless of scenario — process changes)
    proposed_ramp_days  = inputs.proposed_ramp_days
    proposed_ext_ramp   = inputs.proposed_extended_ramp_days
    proposed_recruit    = inputs.proposed_recruitment_cost

    # WFM/QA overhead
    proposed_wfm_count  = inputs.proposed_wfm_fte_count
    proposed_qa_count   = inputs.proposed_qa_fte_count

    # Tech costs
    proposed_ccaas      = inputs.proposed_ccaas_per_agent_month
    auto_contact_cost   = inputs.cost_per_automated_contact * m["auto_contact_cost_factor"]

    proposed = _calc_environment(
        annual_contacts             = inputs.annual_contacts,
        current_automation_pct      = effective_automation,
        agent_count                 = proposed_agent_count,
        hourly_agent_cost           = inputs.hourly_agent_cost,
        burden_rate                 = inputs.burden_rate,
        churn_rate                  = proposed_churn_rate,
        ramp_days                   = proposed_ramp_days,
        extended_ramp_days          = proposed_ext_ramp,
        recruitment_cost            = proposed_recruit,
        wfm_fte_count               = proposed_wfm_count,
        wfm_fte_salary              = inputs.wfm_fte_salary,
        qa_fte_count                = proposed_qa_count,
        qa_fte_salary               = inputs.qa_fte_salary,
        ccaas_cost_per_agent_month  = proposed_ccaas,
        other_tech_annual           = 0,
        contacts_per_agent_per_day  = inputs.contacts_per_agent_per_day,
        work_days_per_year          = inputs.work_days_per_year,
        automated_contacts          = automated_contacts,
        cost_per_automated_contact  = auto_contact_cost,
        wfm_wfo_addon               = inputs.wfm_wfo_addon,
        auto_qa_addon               = inputs.auto_qa_addon,
        sim_training_addon          = inputs.sim_training_addon,
        ai_agent_assist_addon       = inputs.ai_agent_assist_addon,
    )

    # ── ROI ──
    impl_cost        = inputs.implementation_cost * m["impl_cost_factor"]
    base_savings     = current["total_cost"] - proposed["total_cost"]
    annual_savings   = base_savings * m.get("savings_haircut", 1.0)
    net_first_year   = annual_savings - impl_cost
    payback_months   = (
        (impl_cost / (annual_savings / 12))
        if annual_savings > 0 else None
    )
    npv = {
        yr: (annual_savings * yr) - impl_cost
        for yr in [1, 3, 5]
    }

    # ── Cost driver breakdown ──
    savings_by_driver = {
        "Labor reduction":    current["labor_cost"]    - proposed["labor_cost"],
        "Churn reduction":    current["churn_cost"]    - proposed["churn_cost"],
        "Overhead reduction": current["overhead_cost"] - proposed["overhead_cost"],
        "Tech delta":         current["tech_cost"]     - proposed["tech_cost"],
    }
    biggest_driver = max(savings_by_driver, key=savings_by_driver.get)

    return {
        "scenario":           scenario,
        "scenario_label":     m["label"],
        "scenario_color":     m["color"],
        "scenario_desc":      m["description"],
        "current":            current,
        "proposed":           proposed,
        "effective_automation": effective_automation,
        "proposed_agent_count": proposed_agent_count,
        "proposed_churn_rate":  proposed_churn_rate,
        "automated_contacts":   automated_contacts,
        "impl_cost":            impl_cost,
        "annual_savings":       annual_savings,
        "net_first_year":       net_first_year,
        "payback_months":       payback_months,
        "npv":                  npv,
        "savings_by_driver":    savings_by_driver,
        "biggest_driver":       biggest_driver,
    }


# --------------------------------------------------
# Main entry point
# --------------------------------------------------

def run_business_case(inputs: BusinessCaseInputs) -> dict:
    """
    Run all three scenarios and return combined results.

    Returns:
        {
            "inputs":        BusinessCaseInputs,
            "conservative":  scenario_dict,
            "base":          scenario_dict,
            "optimistic":    scenario_dict,
            "summary":       high-level summary dict,
        }
    """
    results = {
        scenario: _run_scenario(inputs, scenario)
        for scenario in ["conservative", "base", "optimistic"]
    }

    base = results["base"]
    summary = {
        "annual_savings_range": (
            results["conservative"]["annual_savings"],
            results["base"]["annual_savings"],
            results["optimistic"]["annual_savings"],
        ),
        "payback_range_months": (
            results["conservative"]["payback_months"],
            results["base"]["payback_months"],
            results["optimistic"]["payback_months"],
        ),
        "five_year_npv_range": (
            results["conservative"]["npv"][5],
            results["base"]["npv"][5],
            results["optimistic"]["npv"][5],
        ),
        "base_annual_savings":  base["annual_savings"],
        "base_payback_months":  base["payback_months"],
        "biggest_driver":       base["biggest_driver"],
        "churn_savings":        base["savings_by_driver"].get("Churn reduction", 0),
        "labor_savings":        base["savings_by_driver"].get("Labor reduction", 0),
        "agent_reduction":      base["current"]["agent_count"] - base["proposed_agent_count"],
        "automation_pct":       base["effective_automation"],
    }

    return {
        "inputs":       inputs,
        "conservative": results["conservative"],
        "base":         results["base"],
        "optimistic":   results["optimistic"],
        "summary":      summary,
    }


# --------------------------------------------------
# Pre-fill helper
# --------------------------------------------------

def _containment_from_flows(session_state: dict) -> float | None:
    """
    Compute weighted average containment target from confirmed flows
    using flow_templates.json data.
    Returns None if no template data available.
    """
    try:
        import json
        from pathlib import Path
        tmpl_path = Path(__file__).parent / "data" / "flow_templates.json"
        with open(tmpl_path) as f:
            templates = json.load(f)
    except Exception:
        return None

    discovery = session_state.get("discovery", [])
    confirmed = [f for f in discovery if f.get("confirmed")]
    if not confirmed:
        return None

    targets = []
    for flow in confirmed:
        fid  = flow.get("flow_id", "")
        tmpl = templates.get(fid, {})
        ct   = tmpl.get("containment_target")
        ctype= tmpl.get("containment_type", "standard")
        # Only include standard containment flows — skip engagement/ai_assisted
        if ct is not None and ctype == "standard":
            targets.append(ct / 100.0)

    if not targets:
        return None

    avg = sum(targets) / len(targets)
    return round(avg, 2)


def _answers_hash(answers: dict) -> str:
    """Simple hash of conv_answers for staleness detection."""
    import hashlib, json
    return hashlib.md5(
        json.dumps(answers, sort_keys=True, default=str).encode()
    ).hexdigest()[:8]


def prefill_from_session(session_state: dict) -> "BusinessCaseInputs":
    """
    Build BusinessCaseInputs from Streamlit session state.
    Pre-fills what we can derive from conversation answers.
    Leaves agent_count as 0 (required user input).

    Uses flow_templates.json containment targets to derive
    target_automation_pct — much more accurate than AI score brackets.
    Stores a hash of conv_answers so staleness can be detected.
    """
    answers    = session_state.get("conv_answers", {})
    bp         = session_state.get("business_profile", {})
    assessment = session_state.get("assessment", {})

    # Volume mapping
    volume_map = {
        "Under 1,000":      500,
        "1,000 – 10,000":   5_000,
        "10,000 – 50,000":  25_000,
        "50,000+":          600_000,
        "Not sure yet":     10_000,
    }
    vol_str = answers.get("volume", "")
    if isinstance(vol_str, str):
        annual_contacts = volume_map.get(vol_str, 10_000)
    else:
        annual_contacts = 10_000

    # Channel mix
    channels = answers.get("channels", [])
    if isinstance(channels, str):
        channels = [channels]
    has_phone = any("phone" in c.lower() for c in channels)
    has_chat  = any("chat" in c.lower() for c in channels)
    if has_phone and has_chat:
        voice_pct, chat_pct = 0.60, 0.40
    elif has_phone:
        voice_pct, chat_pct = 0.90, 0.10
    elif has_chat:
        voice_pct, chat_pct = 0.20, 0.80
    else:
        voice_pct, chat_pct = 0.60, 0.40

    # Current automation
    automation_map = {
        "Mostly manual — agents handle everything": 0.00,
        "Basic IVR — press 1 for sales, etc.":      0.10,
        "Some chatbot or self-service":              0.25,
        "Significant automation already in place":  0.45,
    }
    auto_str = answers.get("automation", "")
    if isinstance(auto_str, list):
        auto_str = auto_str[0] if auto_str else ""
    current_automation = automation_map.get(auto_str, 0.00)

    # CCaaS cost from platform
    cc_platform = answers.get("cc_platform", "")
    if isinstance(cc_platform, list):
        cc_platform = cc_platform[0] if cc_platform else ""
    enterprise_platforms = {"Genesys", "NICE CXone", "Avaya"}
    mid_platforms        = {"Five9", "Cisco", "Twilio Flex"}
    consumption_platforms= {"Amazon Connect"}
    if cc_platform in enterprise_platforms:
        ccaas_cost = 150.0
    elif cc_platform in mid_platforms:
        ccaas_cost = 120.0
    elif cc_platform in consumption_platforms:
        ccaas_cost = 100.0
    else:
        ccaas_cost = 100.0

    # Proposed CCaaS — use vendor shortlist top vendor tier if available
    vendors = session_state.get("vendor_shortlist", [])
    if vendors:
        top_tier = vendors[0].get("tier", "mid-market")
        proposed_ccaas = {"enterprise": 160.0, "mid-market": 130.0,
                          "specialist": 140.0}.get(top_tier, ccaas_cost)
    else:
        proposed_ccaas = ccaas_cost

    # Target automation — use flow templates weighted average (Issue 1 fix)
    # This is far more accurate than generic AI score brackets
    template_target = _containment_from_flows(session_state)
    if template_target is not None:
        target_automation = template_target
    else:
        # Fallback to AI score brackets only when no template data
        ai_score = assessment.get("business_ai_score", 50)
        if ai_score >= 70:
            target_automation = 0.45
        elif ai_score >= 40:
            target_automation = 0.30
        else:
            target_automation = 0.20

    # Implementation cost — scale with volume and complexity
    impl_base = {
        500:    300_000,
        5_000:  500_000,
        25_000: 750_000,
        75_000: 1_200_000,
    }.get(annual_contacts, 500_000)

    result = BusinessCaseInputs(
        annual_contacts         = annual_contacts,
        voice_pct               = voice_pct,
        chat_pct                = chat_pct,
        email_pct               = 0.0,
        current_automation_pct  = current_automation,
        agent_count             = 0,        # required — user must enter
        hourly_agent_cost       = 17.0,
        burden_rate             = 0.18,
        churn_rate              = 0.32,
        ramp_days               = 90,
        extended_ramp_days      = 60,
        recruitment_cost        = 4_000.0,
        wfm_fte_count           = 2,
        wfm_fte_salary          = 55_000.0,
        qa_fte_count            = 1,
        qa_fte_salary           = 55_000.0,
        ccaas_cost_per_agent_month  = ccaas_cost,
        other_tech_annual           = 0.0,
        target_automation_pct       = target_automation,
        proposed_churn_rate         = 0.21,
        proposed_ramp_days          = 60,
        proposed_extended_ramp_days = 30,
        proposed_recruitment_cost   = 2_000.0,
        proposed_wfm_fte_count      = 1,
        proposed_qa_fte_count       = 1,
        cost_per_automated_contact  = 0.50,
        proposed_ccaas_per_agent_month = proposed_ccaas,
        wfm_wfo_addon               = 40.0,
        auto_qa_addon               = 25.0,
        sim_training_addon          = 15.0,
        ai_agent_assist_addon       = 35.0,
        implementation_cost         = float(impl_base),
        analysis_years              = 5,
    )

    # Store hash for staleness detection (Issue 2 fix)
    result._answers_hash = _answers_hash(answers)
    return result