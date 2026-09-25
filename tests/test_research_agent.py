import json

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolMessage

from conftest import load_example

ra = load_example("langchain/01-research-agent/research_agent.py")


class ToolCallingFake(GenericFakeChatModel):
    """Replays scripted replies; accepts tools the way a real chat model does."""

    def bind_tools(self, tools, **kwargs):
        return self


def scripted_model(final_answer):
    return ToolCallingFake(messages=iter([
        AIMessage(content="", tool_calls=[
            {"name": "cerebrus_pulse", "args": {"coin": "BTC"}, "id": "call_1"}]),
        AIMessage(content=final_answer),
    ]))


def run(api, model):
    agent = ra.build_agent(model, ra.make_client())
    return agent.invoke({"messages": [{"role": "user", "content": "Is BTC overbought?"}]})


def test_dry_run_needs_no_model_and_pays_nothing(api, capsys):
    assert ra.main(["--dry-run"]) == 0
    assert api.paths == ["/health"]
    out = capsys.readouterr().out
    assert "cerebrus_list_coins         free" in out
    assert "cerebrus_pulse            $0.025" in out
    assert "cerebrus_screener          $0.06" in out
    assert "API status: ok" in out


def test_the_agent_calls_a_tool_and_answers(api):
    result = run(api, scripted_model("BTC RSI (1h) is 49.2: neutral, not overbought."))
    assert api.paid_paths == ["/pulse/BTC"]
    tool_msg = next(m for m in result["messages"] if isinstance(m, ToolMessage))
    assert json.loads(tool_msg.content)["timeframes"]["1h"]["indicators"]["rsi_14"] == 49.16
    assert result["messages"][-1].content.startswith("BTC RSI (1h) is 49.2")


def test_an_unpaid_tool_hands_the_agent_the_price(api):
    api.unpaid = True
    result = run(api, scripted_model("I could not get BTC data without payment ($0.025)."))
    tool_msg = next(m for m in result["messages"] if isinstance(m, ToolMessage))
    body = json.loads(tool_msg.content)
    assert body["payment_required"] is True
    assert body["price_usd"] == "0.025"


def test_ask_returns_the_final_message(api):
    agent = ra.build_agent(scripted_model("Neutral."), ra.make_client())
    assert ra.ask(agent, "Is BTC overbought?") == "Neutral."


def test_no_question_prints_usage(api, capsys):
    assert ra.main([]) == 0
    assert api.paths == []
    assert 'python research_agent.py "Is BTC overbought?"' in capsys.readouterr().out
