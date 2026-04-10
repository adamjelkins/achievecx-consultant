"""
api/routes/blueprint.py
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from core.session_store import get_or_create_session, save_session

router = APIRouter()


def _normalize_bc_results(bc: dict) -> dict:
    """Convert string NPV keys back to integers after JSON round-trip."""
    if not bc:
        return bc
    for scenario in ('conservative', 'base', 'optimistic'):
        s = bc.get(scenario, {})
        if 'npv' in s and isinstance(s['npv'], dict):
            s['npv'] = {int(k): v for k, v in s['npv'].items()}
    return bc


def _shim_session_state(session):
    import sys, types

    class DictNamespace(dict):
        def __getattr__(self, k): return self.get(k)
        def __setattr__(self, k, v): self[k] = v

    st_mock = types.ModuleType('streamlit')
    st_mock.spinner = lambda x: __import__('contextlib').nullcontext()
    st_mock.error   = lambda x: None
    st_mock.warning = lambda x: None
    st_mock.info    = lambda x: None

    ns = DictNamespace()
    ns['business_profile']      = session.business_profile or {}
    ns['discovery']             = session.discovery or []
    ns['conv_answers']          = session.conv_answers or {}
    ns['assessment']            = session.assessment or {}
    ns['risk_assessment']       = session.risk_assessment or {}
    ns['business_case_results'] = _normalize_bc_results(session.business_case_results or {})
    ns['intake_profile']        = session.intake_data or {
        'first_name':   'John',
        'last_name':    'Doe',
        'email':        'john.doe@att.com',
        'company_name': (session.business_profile or {}).get('company_name', ''),
    }
    ns['vendor_shortlist']      = session.vendor_shortlist or []
    ns['discovery_profile']     = session.discovery_profile or {}

    st_mock.session_state = ns
    sys.modules['streamlit'] = st_mock
    return st_mock


@router.post("/{session_id}/generate")
async def generate_blueprint(session_id: str):
    session = await get_or_create_session(session_id)
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        _shim_session_state(session)
        from blueprint_generator import generate_blueprint as _generate
        result = _generate()

        # Enrich flow_cards with template data from scored_flows
        try:
            score_map = {
                f.get('flow_id'): f
                for f in (session.assessment or {}).get('scored_flows', [])
            }
            # Also build name lookup from scored flows
            name_map = {
                f.get('flow_name', '').lower(): f
                for f in (session.assessment or {}).get('scored_flows', [])
            }
            for card in result.get('flow_cards', []):
                scored = (score_map.get(card.get('flow_id')) or
                          name_map.get(card.get('flow_name', '').lower()) or {})
                for field in ['entry_channels', 'data_sources', 'human_role',
                              'human_detail', 'intents', 'output_actions',
                              'authentication', 'complexity', 'contain_display',
                              'contain_label', 'rationale']:
                    if not card.get(field) and scored.get(field):
                        card[field] = scored[field]
        except Exception as e:
            print(f'[blueprint] Flow card enrichment failed: {e}')

        session.blueprint        = result
        session.phase_4_complete = True
        await save_session(session)
        return result

    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(500, f"Blueprint generation failed: {e}")


@router.get("/{session_id}")
async def get_blueprint(session_id: str):
    session = await get_or_create_session(session_id)
    if not session.blueprint:
        raise HTTPException(404, "No blueprint found — generate it first")
    return session.blueprint


@router.get("/{session_id}/pdf")
async def download_blueprint_pdf(session_id: str, theme: str = "light"):
    session = await get_or_create_session(session_id)
    if not session.blueprint:
        raise HTTPException(404, "No blueprint found — generate it first")

    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from pdf_generator import generate_pdf

        pdf_bytes = generate_pdf(session.blueprint, theme_name=theme)

        company   = session.blueprint.get("company_name", "Blueprint").replace(" ", "_")
        date_str  = session.blueprint.get("generated_at", "")[:10]
        filename  = f"CX_Blueprint_{company}_{date_str}_{theme}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(500, f"PDF generation failed: {e}")