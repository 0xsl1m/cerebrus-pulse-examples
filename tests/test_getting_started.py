from conftest import load_example

gs = load_example("python/01-getting-started/getting_started.py")


def test_dry_run_calls_only_free_endpoints(api, capsys):
    assert gs.main(["--dry-run"]) == 0
    assert api.paths == ["/health", "/demo/BTC"]
    out = capsys.readouterr().out
    assert "API status: ok (version 1.4.0)" in out
    assert "BTC price: $84,512.50" in out
    assert " 1h  RSI 49.2 (neutral), trend weak_bullish" in out
    assert "Confluence: 0.62 on a 0-1 scale, bullish" in out
    assert "about $0.045 USDC" in out


def test_dry_run_ignores_a_wallet_key(api, monkeypatch):
    monkeypatch.setenv("CEREBRUS_WALLET_KEY", "not-a-key")  # would raise if it were used
    assert gs.main(["--dry-run"]) == 0
    assert api.paid_paths == []


def test_paid_run_parses_every_response(api, capsys):
    api.routes["/coins"] = {"coins": ["BTC", "ETH", "SOL"], "count": 3}
    assert gs.main(["btc"]) == 0
    assert api.paid_paths == ["/pulse/BTC", "/sentiment", "/funding/BTC"]
    out = capsys.readouterr().out
    assert "Tracking 3 coins, for example BTC, ETH, SOL" in out
    assert "Market sentiment: bullish" in out
    # 1.25e-05 per hour x 24 x 365 = 10.95% a year
    assert "Funding: 0.00125% per hour, 10.95% annualized" in out


def test_without_a_wallet_it_reports_the_price_and_stops(api, capsys):
    api.unpaid = True
    api.routes["/coins"] = {"coins": ["BTC"], "count": 1}
    assert gs.main([]) == 2
    assert api.paid_paths == ["/pulse/BTC"]  # stops at the first 402
    out = capsys.readouterr().out
    assert "The API asks $0.025 USDC on eip155:8453" in out
    assert "--dry-run" in out
