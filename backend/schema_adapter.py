"""
schema_adapter.py

Updated: reads crm and cc_platform as separate conv_answers keys.
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
from datetime import datetime
from typing import Any

from streamlit_app.discovery.schema import (
    DiscoveryProfile,
    DiscoverySection,
    DiscoveryField,
)

SOURCE_CONFIDENCE = {
    "gpt_inferred": 0.65,
    "user_stated":  0.90,
    "user_typed":   0.85,
    "confirmed":    1.00,
}


def _field(field_id, label, value, source="user_stated", required=False):
    conf = SOURCE_CONFIDENCE.get(source, 0.5)
    if value is None or value == "" or value == []:
        conf = 0.0
    return DiscoveryField(
        field_id=field_id, label=label, value=value,
        confidence=conf, required=required,
        source=source, last_updated=datetime.utcnow(),
    )


def _inferred(field_id, label, value, required=False):
    return _field(field_id, label, value, "gpt_inferred", required)


def _stated(field_id, label, value, required=False, typed=False):
    return _field(field_id, label, value,
                  "user_typed" if typed else "user_stated", required)


# --------------------------------------------------
# Section builders
# --------------------------------------------------

def _build_business_context(bp: dict, answers: dict) -> DiscoverySection:
    return DiscoverySection(
        section_id="business_context",
        title="Business Context",
        required_fields=["business_name", "industry", "regions_served"],
        confidence=0.0,
        fields={
            "business_name": _inferred(
                "business_name", "Business Name",
                bp.get("company_name", ""), required=True),
            "industry": _inferred(
                "industry", "Industry",
                bp.get("industry", ""), required=True),
            "regions_served": _stated(
                "regions_served", "Regions Served",
                answers.get("regions") or None, required=True),
            "business_size": _inferred(
                "business_size", "Business Size",
                bp.get("size_estimate", "")),
            "description": _inferred(
                "description", "Description",
                bp.get("description", "")),
            "channels": _stated(
                "channels", "Channels",
                answers.get("channels") or None),
            "volume_estimate": _stated(
                "volume_estimate", "Monthly Volume",
                answers.get("volume") or None),
            "pain_points": _stated(
                "pain_points", "Pain Points",
                answers.get("pain_point") or None,
                typed=isinstance(answers.get("pain_point"), str)
                      and len(str(answers.get("pain_point", ""))) > 30),
            "automation_level": _stated(
                "automation_level", "Automation Level",
                answers.get("automation") or None),
            "primary_goal": _stated(
                "primary_goal", "Primary Goal",
                answers.get("goal") or None,
                typed=isinstance(answers.get("goal"), str)
                      and len(str(answers.get("goal", ""))) > 30),
            "timeline": _stated(
                "timeline", "Timeline",
                answers.get("timeline") or None),
        },
    )


def _build_systems_of_record(answers: dict) -> DiscoverySection:
    """
    Now reads crm and cc_platform as separate answer keys.
    No classification logic needed.
    """
    crm_val = answers.get("crm") or None
    cc_val  = answers.get("cc_platform") or None

    return DiscoverySection(
        section_id="systems_of_record",
        title="Systems of Record",
        required_fields=["crm"],
        confidence=0.0,
        fields={
            "crm": _stated(
                "crm", "CRM / System of Record",
                crm_val, required=True,
                typed=isinstance(crm_val, str) and crm_val not in {
                    "Salesforce", "HubSpot", "Microsoft Dynamics",
                    "ServiceNow", "Zendesk", "SAP CRM", "Oracle CX",
                }),
            "contact_center_platform": _stated(
                "contact_center_platform", "Contact Center Platform",
                cc_val,
                typed=isinstance(cc_val, str) and cc_val not in {
                    "Genesys", "NICE CXone", "Avaya", "Five9",
                    "Amazon Connect", "Cisco", "Twilio Flex",
                }),
            "ticketing": _field(
                "ticketing", "Ticketing System", None, "unknown"),
        },
    )


def _build_customer_types(bp: dict) -> DiscoverySection:
    industry = bp.get("industry", "")
    b2b = {"Technology", "Financial Services", "Insurance",
           "Logistics", "Manufacturing", "Professional Services"}
    b2c = {"Retail", "Healthcare", "Hospitality", "Telecom", "Education"}

    if industry in b2b:
        primary = "Business customers (B2B)"
    elif industry in b2c:
        primary = "Consumers (B2C)"
    else:
        primary = "Mixed (B2B and B2C)"

    return DiscoverySection(
        section_id="customer_types",
        title="Customer Types",
        required_fields=["primary_customers"],
        confidence=0.0,
        fields={
            "primary_customers": _inferred(
                "primary_customers", "Primary Customer Types",
                primary, required=True),
            "secondary_customers": _field(
                "secondary_customers", "Secondary", None, "unknown"),
            "authentication_required": _field(
                "authentication_required", "Auth Required", None, "unknown"),
        },
    )


def _build_compliance(bp: dict) -> DiscoverySection:
    industry = bp.get("industry", "")
    regulated = {
        "Healthcare":         "HIPAA",
        "Financial Services": "PCI-DSS, SOX",
        "Insurance":          "State insurance regulations",
        "Government":         "FISMA, FedRAMP",
        "Education":          "FERPA",
    }
    standard = regulated.get(industry, "")

    return DiscoverySection(
        section_id="compliance",
        title="Compliance & Risk",
        required_fields=[],
        confidence=0.0,
        fields={
            "regulated_industry": _inferred(
                "regulated_industry", "Regulated", bool(standard)),
            "standards": _inferred(
                "standards", "Standards", standard or None),
            "data_sensitivity": _inferred(
                "data_sensitivity", "Data Sensitivity",
                "High" if standard else "Standard"),
        },
    )


# --------------------------------------------------
# Main entry point
# --------------------------------------------------

def build_profile_from_session() -> DiscoveryProfile:
    bp      = st.session_state.get("business_profile", {})
    answers = st.session_state.get("conv_answers", {})

    profile = DiscoveryProfile(
        sections={
            "business_context":  _build_business_context(bp, answers),
            "systems_of_record": _build_systems_of_record(answers),
            "customer_types":    _build_customer_types(bp),
            "compliance":        _build_compliance(bp),
        }
    )

    try:
        from streamlit_app.discovery.confidence import refresh_profile_confidence
        profile = refresh_profile_confidence(profile)
    except Exception as e:
        print(f"[schema_adapter] Confidence refresh failed: {e}")

    st.session_state.discovery_profile = profile
    return profile


def get_profile() -> DiscoveryProfile | None:
    if not st.session_state.get("discovery_profile"):
        return build_profile_from_session()
    return st.session_state.discovery_profile


def profile_summary_for_gpt() -> dict:
    profile = get_profile()
    if not profile:
        return {}

    summary = {
        "profile_confidence": profile.profile_confidence,
        "status":             profile.status,
    }
    for section_id, section in profile.sections.items():
        for field_id, field in section.fields.items():
            if field.value is not None and field.value != "":
                summary[f"{section_id}.{field_id}"] = {
                    "value":      field.value,
                    "confidence": field.confidence,
                    "source":     field.source,
                }
    return summary