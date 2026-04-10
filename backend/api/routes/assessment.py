"""
api/routes/assessment.py
"""
from fastapi import APIRouter, HTTPException
from core.session_store import get_or_create_session, save_session

router = APIRouter()


def _mock_streamlit(session):
    """Mock st.session_state before importing streamlit-dependent modules."""
    import sys, types
    if 'streamlit' not in sys.modules:
        st_mock = types.ModuleType('streamlit')
        st_mock.session_state = types.SimpleNamespace()
        # Mock other streamlit functions used in modules
        st_mock.spinner = lambda x: __import__('contextlib').nullcontext()
        st_mock.error   = lambda x: None
        st_mock.warning = lambda x: None
        st_mock.info    = lambda x: None
        sys.modules['streamlit'] = st_mock
    try:
        import streamlit as st
    except ImportError:
        import sys as _sys
        st = _sys.modules['streamlit']
    if session:
        st.session_state.business_profile = session.business_profile
        st.session_state.discovery        = session.discovery
        st.session_state.conv_answers     = session.conv_answers
        st.session_state.assessment       = session.assessment


@router.post("/{session_id}/run")
async def run_assessment(session_id: str):
    """Run AI maturity assessment. Caches result in session."""
    session = await get_or_create_session(session_id)

    confirmed = [f for f in session.discovery if f.get("confirmed")]
    if not confirmed:
        raise HTTPException(400, "No confirmed flows to assess")

    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        _mock_streamlit(session)
        from maturity_assessment import run_assessment as _run

        # Enrich confirmed flows with template data BEFORE scoring
        # so _score_flow gets the correct category
        try:
            import json
            tmpl_path = Path(__file__).parent.parent.parent / 'data' / 'flow_templates.json'
            with open(tmpl_path) as f:
                templates = json.load(f)
            name_lookup = {
                v.get('flow_name', '').lower(): v
                for v in templates.values()
            }

            KEYWORD_CATEGORY = {
                'billing': 'Billing', 'payment': 'Billing', 'invoice': 'Billing',
                'order': 'Order Management', 'shipment': 'Order Management',
                'delivery': 'Order Management', 'tracking': 'Order Management',
                'status': 'Order Management',
                'technical': 'Technical Support', 'outage': 'Technical Support',
                'troubleshoot': 'Technical Support',
                'support': 'Customer Care', 'complaint': 'Customer Care',
                'faq': 'Customer Care', 'general': 'Customer Care',
                'account': 'Account Services', 'activation': 'Account Services',
                'changes': 'Account Services', 'update': 'Account Services',
                'password': 'Authentication & Security',
                'retention': 'Customer Lifecycle', 'win-back': 'Customer Lifecycle',
                'upsell': 'Sales Support', 'sales': 'Sales Support',
                'appointment': 'Scheduling', 'schedule': 'Scheduling',
                'notification': 'Proactive Communications', 'alert': 'Proactive Communications',
                'reminder': 'Proactive Communications',
            }

            def _infer_category(flow_name: str) -> str:
                nl = flow_name.lower()
                for kw, cat in KEYWORD_CATEGORY.items():
                    if kw in nl:
                        return cat
                return ''
            for flow in confirmed:
                fid  = flow.get('flow_id', '')
                # Skip ID lookup — sequential IDs don't match canonical template IDs
                tmpl = name_lookup.get(flow.get('flow_name', '').lower())
                # Apply template data if found, keyword category as fallback
                # Override if category is missing or generic
                if not flow.get('category') or flow.get('category') in ('General', 'Unknown', ''):
                    if tmpl:
                        flow['category'] = tmpl.get('category', '')
                    if not flow.get('category') or flow.get('category') in ('General', 'Unknown', ''):
                        flow['category'] = _infer_category(flow.get('flow_name', ''))
                if tmpl:
                    if not flow.get('entry_channels'):
                        flow['entry_channels'] = tmpl.get('entry_channels', [])
                    if not flow.get('data_sources'):
                        flow['data_sources']   = tmpl.get('data_sources', [])
                    if not flow.get('human_role'):
                        flow['human_role']     = tmpl.get('human_role', '')
                    if not flow.get('complexity'):
                        flow['complexity']     = tmpl.get('complexity', '')
                    flow['human_detail']   = tmpl.get('human_role_detail', '')
                    flow['intents']        = tmpl.get('intents', [])
                    flow['output_actions'] = tmpl.get('output_actions', [])
                    flow['authentication'] = tmpl.get('authentication', '')
                else:
                    # No template match — still set keyword category
                    if not flow.get('category'):
                        flow['category'] = _infer_category(flow.get('flow_name', ''))
        except Exception as te:
            print(f'[assessment] Pre-enrichment failed: {te}')

        result = _run(confirmed, session.business_profile)

        # Also enrich scored_flows in result (preserves any extra fields)
        try:
            for flow in result.get('scored_flows', []):
                fid  = flow.get('flow_id', '')
                # Skip ID lookup — sequential IDs don't match canonical template IDs
                tmpl = name_lookup.get(flow.get('flow_name', '').lower())
                # Apply template data if found, keyword category as fallback
                # Override if category is missing or generic
                if not flow.get('category') or flow.get('category') in ('General', 'Unknown', ''):
                    if tmpl:
                        flow['category'] = tmpl.get('category', '')
                    if not flow.get('category') or flow.get('category') in ('General', 'Unknown', ''):
                        flow['category'] = _infer_category(flow.get('flow_name', ''))
                if tmpl:
                    if not flow.get('entry_channels'):
                        flow['entry_channels'] = tmpl.get('entry_channels', [])
                    if not flow.get('data_sources'):
                        flow['data_sources']   = tmpl.get('data_sources', [])
                    if not flow.get('human_role'):
                        flow['human_role']     = tmpl.get('human_role', '')
                    if not flow.get('complexity'):
                        flow['complexity']     = tmpl.get('complexity', '')
                    flow['human_detail']   = tmpl.get('human_role_detail', '')
                    flow['intents']        = tmpl.get('intents', [])
                    flow['output_actions'] = tmpl.get('output_actions', [])
                    flow['authentication'] = tmpl.get('authentication', '')
                else:
                    # No template match — still set keyword category
                    if not flow.get('category'):
                        flow['category'] = _infer_category(flow.get('flow_name', ''))
        except Exception as te:
            print(f'[assessment] Post-enrichment failed: {te}')

        session.assessment       = result
        session.phase_3_complete = True
        session.current_phase    = "3r"
        await save_session(session)
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Assessment failed: {e}")


@router.get("/{session_id}")
async def get_assessment(session_id: str):
    session = await get_or_create_session(session_id)
    if not session.assessment:
        raise HTTPException(404, "No assessment found — run it first")
    return session.assessment