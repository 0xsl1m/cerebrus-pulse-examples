import copy

import httpx

from conftest import RESPONSES, load_example

sc = load_example("python/05-divergence-scanner/scanner.py")


def test_dry_run_reads_funding_from_the_free_demo(api, capsys):
    assert sc.main(["--dry-run", "BTC"]) == 0
    assert api.paths == ["/demo/BTC"]
    out = capsys.readouterr().out
    assert "costs about $0.03 USDC" in out
    # 1.25e-05 per hour is 10.95% a year
    assert "BTC              -  -          +0.00125%   +10.95" in out
    assert "Not checked: CEX-DEX data is paid only" in out
    assert "tightly arbitraged" not in out  # no CEX-DEX call was made
    assert "Total: 0 divergences, 0 extreme funding" in out


def test_dry_run_stays_inside_the_demo_rate_limit(api):
    sc.main(["--dry-run", "BTC", "ETH", "SOL", "LINK"])
    assert api.paths == ["/demo/BTC", "/demo/ETH", "/demo/SOL"]


def test_paid_scan_flags_divergence_and_extreme_funding(api, capsys):
    hot = copy.deepcopy(RESPONSES["/funding/BTC"])
    hot.update(coin="LINK", current=0.0001)  # 0.01% an hour = 87.6% a year
    api.routes["/funding/LINK"] = hot
    api.routes["/cex-dex/SOL"] = httpx.Response(
        400, json={"detail": "No CEX-DEX data for 'SOL'. Available tokens: ['BTC', 'ETH']"})

    assert sc.main(["BTC", "LINK", "SOL", "--min-divergence-bps", "30"]) == 0
    assert api.paid_paths == ["/cex-dex/BTC", "/funding/BTC", "/cex-dex/LINK",
                              "/funding/LINK", "/cex-dex/SOL", "/funding/SOL"]
    out = capsys.readouterr().out
    assert "Scanning 3 coin(s): about $0.09 USDC." in out
    assert "SOL: no CEX-DEX data (HTTP 400" in out
    assert "SOL: no funding data (HTTP 404" in out
    assert "LINK: -32.6 bps (DEX premium)" in out  # |-32.6| >= 30
    assert "Based on 2 of 3 coin(s); the others have no CEX-DEX data" in out
    assert "Based on 2 of 3 coin(s); the others have no funding data" in out
    assert "BTC: +4.3" not in out  # 4.3 bps is under the threshold
    assert "LINK: +0.01000%/h (+87.6% a year) - crowded long" in out
    assert "Total: 1 divergences, 1 extreme funding" in out


def test_a_402_stops_the_scan(api, capsys):
    api.unpaid = True
    assert sc.main([]) == 2
    assert api.paid_paths == ["/cex-dex/BTC"]
    out = capsys.readouterr().out
    assert "The API asks $0.02 USDC" in out
    assert "set CEREBRUS_WALLET_KEY to pay" in out
    assert "CEX-DEX DIVERGENCES" not in out  # nothing was scanned, so no report


def test_a_spend_limit_mid_scan_keeps_the_rows_already_paid_for(wallet, monkeypatch, capsys):
    monkeypatch.setenv("CEREBRUS_MAX_SPEND_USD", "0.05")
    assert sc.main(["BTC", "ETH", "SOL"]) == 2
    signed = [r.url.path for r in wallet.requests if r.headers.get("PAYMENT-SIGNATURE")]
    assert signed == ["/cex-dex/BTC", "/funding/BTC", "/cex-dex/ETH"]
    assert wallet.paid_paths[-1] == "/funding/ETH"  # refused unsigned; SOL never asked
    out = capsys.readouterr().out
    assert "  BTC           +4.3  CEX        +0.00125%   +10.95" in out
    assert "  ETH           +4.0  CEX                -        -" in out
    assert "budget reached" in out
    assert "Nothing was signed" in out and "CEREBRUS_MAX_SPEND_USD" in out
    assert "CEREBRUS_WALLET_KEY" not in out  # the wallet is set and paid
    assert "The scan stopped early: the table covers 2 of 3 coin(s)." in out
    assert "Spent by this run: $0.05 USDC" in out


def test_no_market_conclusion_without_data(api, capsys):
    not_covered = httpx.Response(400, json={"detail": "No CEX-DEX data. Available tokens: []"})
    api.routes["/cex-dex/BTC"] = api.routes["/cex-dex/ETH"] = not_covered

    assert sc.main(["BTC", "ETH"]) == 0  # /funding/ETH has no fixture: 404
    out = capsys.readouterr().out
    assert "No CEX-DEX data for any coin" in out
    assert "tightly arbitraged" not in out
    assert "None found - funding rates are balanced" in out  # BTC funding is 10.95% a year
    assert "Based on 1 of 2 coin(s); the others have no funding data" in out
    assert "Total: 0 divergences, 0 extreme funding" in out


def test_no_funding_conclusion_without_funding_data(api, capsys):
    api.routes.pop("/funding/BTC")
    assert sc.main(["BTC"]) == 0
    out = capsys.readouterr().out
    assert "No funding data for any coin" in out
    assert "balanced" not in out
