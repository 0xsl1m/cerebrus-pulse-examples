import json

from conftest import RESPONSES, load_example

lh = load_example("python/03-liquidation-heatmap/liquidation_heatmap.py")


def test_dry_run_only_checks_health(api, capsys):
    assert lh.main(["--dry-run", "BTC", "ETH"]) == 0
    assert api.paths == ["/health"]
    out = capsys.readouterr().out
    assert "API status: ok" in out
    assert "liquidations() for BTC, ETH: about $0.06 USDC" in out


def test_heatmap_renders_zones_around_the_price(api, capsys):
    assert lh.main(["btc"]) == 0
    assert api.paid_paths == ["/liquidations/BTC"]
    out = capsys.readouterr().out
    lines = out.splitlines()
    now = next(i for i, line in enumerate(lines) if "<- price now" in line)
    shorts = [line for line in lines[:now] if line.strip().startswith("short")]
    longs = [line for line in lines[now:] if line.strip().startswith("long")]
    assert len(shorts) == 3 and len(longs) == 3
    assert "97,451.55" in shorts[0] and "85,690.15" in shorts[-1]  # highest first
    assert "83,589.90" in longs[0] and "78,129.26" in longs[-1]
    assert "648,820,108" in out and "#" * lh.BAR_WIDTH in out  # the largest zone fills the bar
    assert "Cascade risk:       HIGH" in out
    assert "Long:short split:   65:35" in out
    assert "Nearest cluster:    long liquidations at $83,589.90, 1.09% away" in out


def test_json_prints_the_raw_response(api, capsys):
    assert lh.main(["BTC", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == RESPONSES["/liquidations/BTC"]


def test_an_error_for_one_coin_does_not_stop_the_others(api, capsys):
    assert lh.main(["NOPE", "BTC"]) == 1
    assert api.paid_paths == ["/liquidations/NOPE", "/liquidations/BTC"]
    out = capsys.readouterr().out
    assert "NOPE: error - HTTP 404" in out
    assert "Cascade risk:       HIGH" in out


def test_without_a_wallet_it_reports_the_price(api, capsys):
    api.unpaid = True
    assert lh.main(["BTC"]) == 2
    assert "The API asks $0.03 USDC" in capsys.readouterr().out


def test_a_spend_limit_is_explained_without_asking_for_a_wallet(wallet, monkeypatch, capsys):
    monkeypatch.setenv("CEREBRUS_MAX_SPEND_USD", "0")
    assert lh.main(["BTC"]) == 2
    assert not any(r.headers.get("PAYMENT-SIGNATURE") for r in wallet.requests)
    out = capsys.readouterr().out
    assert "Nothing was signed" in out and "CEREBRUS_MAX_SPEND_USD" in out
    assert "CEREBRUS_WALLET_KEY" not in out
