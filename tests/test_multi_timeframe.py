import copy

from conftest import RESPONSES, load_example

mt = load_example("python/02-multi-timeframe/multi_timeframe.py")


def test_dry_run_reads_the_free_demo(api, capsys):
    assert mt.main(["--dry-run", "btc"]) == 0
    assert api.paths == ["/demo/BTC"]
    out = capsys.readouterr().out
    assert "BTC @ $84,512.50" in out
    assert "RSI 14               49.16         52.40" in out
    assert "Trend         weak_bullish  weak_bullish" in out
    assert "Alignment:  ALL BULLISH (1h, 4h)" in out
    assert "costs about $0.025 USDC" in out


def test_dry_run_stays_inside_the_demo_rate_limit(api, capsys):
    mt.main(["--dry-run", "BTC", "ETH", "SOL", "DOGE"])
    assert api.paths == ["/demo/BTC", "/demo/ETH", "/demo/SOL"]
    assert api.paid_paths == []


def test_paid_run_asks_for_1d_and_marks_missing_timeframes(api, capsys):
    assert mt.main(["BTC"]) == 0
    assert api.paid_paths == ["/pulse/BTC"]
    assert api.requests[0].url.params["timeframes"] == "1h,4h,1d"
    out = capsys.readouterr().out
    # The fixture has no 1d candles: the column shows "-" instead of crashing.
    assert "RSI 14               49.16         52.40             -" in out
    assert "Bias               bullish       bullish             -" in out


def test_mixed_trends_are_flagged(api, capsys):
    pulse = copy.deepcopy(RESPONSES["/pulse/BTC"])
    pulse["timeframes"]["4h"]["indicators"]["trend"] = {
        "direction": -1, "label": "bearish", "ema_stack": "bearish"}
    api.routes["/pulse/ETH"] = pulse
    mt.main(["ETH"])
    assert "MIXED (1h weak_bullish, 4h bearish) - use caution" in capsys.readouterr().out


def test_without_a_wallet_it_reports_the_price(api, capsys):
    api.unpaid = True
    assert mt.main(["BTC", "ETH"]) == 2
    assert api.paid_paths == ["/pulse/BTC"]
    assert "The API asks $0.025 USDC" in capsys.readouterr().out
