from app.agent import deterministic_analysis, validate_po, validate_created_po

def test_recommendation_is_modified():
    r=deterministic_analysis('recommendation_review')
    assert r['decision']=='MODIFY'
    assert r['proposed_orders'][0]['qty']==300
    assert r['validation']['acceptable'] is True

def test_supplier_shortage_splits_order():
    r=deterministic_analysis('supplier_shortage')
    assert r['decision']=='MODIFY'
    assert [o['qty'] for o in r['proposed_orders']]==[250,250]
    assert r['proposed_orders'][1]['supplier_id']=='SUP-ALT'

def test_forecast_change_recalculates_need_and_hits_budget_constraint():
    r=deterministic_analysis('forecast_change')
    assert r['evidence']['forecast']['forecast_7d']==977
    assert r['evidence']['calculation']['recommended_qty']==687
    assert r['decision']=='INVESTIGATE'
    assert r['proposed_orders']==[]

def test_constraint_blocks_execution():
    r=deterministic_analysis('constraint')
    assert r['decision']=='INVESTIGATE'
    assert r['validation']['acceptable'] is False
    assert any('budget' in e.lower() for e in r['validation']['errors'])

def test_post_action_validation_detects_mismatch():
    po={'created':True,'qty':301,'supplier_id':'SUP-APL','status':'PENDING_SUPPLIER_CONFIRMATION'}
    r=validate_created_po(po,300,'SUP-APL')
    assert r['acceptable'] is False
    assert 'Approved quantity preserved' in r['errors']


def test_llm_tool_calling_path_uses_model_proposal_and_guardrails(monkeypatch):
    import json
    import sys
    import types
    import app.agent as agent

    class Item:
        def __init__(self, typ, **kwargs):
            self.type = typ
            self.__dict__.update(kwargs)

    class Response:
        def __init__(self, output, output_text=""):
            self.output = output
            self.output_text = output_text

    class FakeResponses:
        def __init__(self):
            self.calls = 0

        def create(self, **kwargs):
            self.calls += 1
            assert kwargs["tools"]
            assert kwargs["text"]["format"]["name"] == "procurement_decision"
            if self.calls == 1:
                return Response([
                    Item(
                        "function_call",
                        name="get_inventory",
                        arguments=json.dumps({"sku": "SKU-APPLE-001"}),
                        call_id="call-1",
                    )
                ])
            proposal = {
                "decision": "MODIFY",
                "action": "Prepare a 300-unit PO after buyer approval.",
                "rationale": ["The tool evidence supports 300 incremental units."],
                "proposed_orders": [{
                    "qty": 300,
                    "supplier_id": "SUP-APL",
                    "supplier_name": "FreshFarm Foods",
                }],
            }
            return Response([Item("message")], json.dumps(proposal))

    fake_openai = types.SimpleNamespace(
        OpenAI=lambda api_key: types.SimpleNamespace(responses=FakeResponses())
    )
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.6-luna")

    result = agent.run_llm_agent("recommendation_review")
    assert result["agent_mode"] == "openai-tool-calling + deterministic-guardrail"
    assert result["decision"] == "MODIFY"
    assert result["proposed_orders"][0]["qty"] == 300
    assert result["llm_guardrail"]["acceptable"] is True
    assert len(result["llm_tool_log"]) == 1


def test_llm_proposal_that_ignores_evidence_is_blocked(monkeypatch):
    import json
    import sys
    import types
    import app.agent as agent

    class Item:
        def __init__(self, typ, **kwargs):
            self.type = typ
            self.__dict__.update(kwargs)

    class Response:
        def __init__(self, output, output_text=""):
            self.output = output
            self.output_text = output_text

    class FakeResponses:
        def __init__(self):
            self.calls = 0

        def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return Response([
                    Item(
                        "function_call",
                        name="get_constraints",
                        arguments=json.dumps({"sku": "SKU-APPLE-001"}),
                        call_id="call-1",
                    )
                ])
            proposal = {
                "decision": "ACCEPT",
                "action": "Buy the original 800 units.",
                "rationale": ["The original recommendation is 800 units."],
                "proposed_orders": [{
                    "qty": 800,
                    "supplier_id": "SUP-APL",
                    "supplier_name": "FreshFarm Foods",
                }],
            }
            return Response([Item("message")], json.dumps(proposal))

    fake_openai = types.SimpleNamespace(
        OpenAI=lambda api_key: types.SimpleNamespace(responses=FakeResponses())
    )
    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    result = agent.run_llm_agent("recommendation_review")
    assert result["llm_proposal"]["decision"] == "ACCEPT"
    assert result["llm_guardrail"]["acceptable"] is False
    assert result["decision"] == "MODIFY"
    assert result["proposed_orders"][0]["qty"] == 300
