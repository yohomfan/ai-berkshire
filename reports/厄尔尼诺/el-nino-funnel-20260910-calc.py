"""Reproduce the dated screening calculations; inputs are cited in the report."""

from decimal import Decimal as D, getcontext
from pathlib import Path
import json
import subprocess
import sys

getcontext().prec = 28
ROOT = Path(__file__).resolve().parents[2]

cases = {
    "haier": {
        "price": "21.30", "shares": "9303088164",
        "annual_parent_profit": "19553000000",
        "half_parent_profit": "10316254946.26",
        "prior_half_parent_profit": "12033000000",
        "half_ocf": "9752033977.71", "annual_roe": "16.98",
        "liabilities_pct": "58.52",
    },
    "cosco": {
        "price": "16.46", "shares": "15268122965",
        "annual_parent_profit": "30868147821.38",
        "half_parent_profit": "13418920777.40",
        "prior_half_parent_profit": "17536092241.00",
        "half_ocf": "23330225726.57", "annual_roe": "13.17",
        "liabilities_pct": "41.01",
    },
    "sugar": {
        "price": "19.80", "shares": "2138848228",
        "annual_parent_profit": "951225734.55",
        "half_parent_profit": "608343069.77",
        "prior_half_parent_profit": "444859639.76",
        "half_ocf": "1198390331.94", "annual_roe": "8.24",
        "liabilities_pct": str(D("7352451233.45") / D("18812707588.43") * 100),
    },
}

out = {"notes": [
    "CFO/parent profit is a screening proxy, not cash conversion attributable solely to common shareholders.",
    "A-share price times total shares is A-price-equivalent capitalization, not sum-of-share-classes market capitalization.",
    "Haier annual and prior-half profits use rounded published values.",
    "Cosco price is a September 9 intraday snapshot, not a verified closing price.",
]}
logs = []
for name, v in cases.items():
    ttm = D(v["annual_parent_profit"]) + D(v["half_parent_profit"]) - D(v["prior_half_parent_profit"])
    eps = ttm / D(v["shares"])
    out[name] = dict(v, ttm_profit=str(ttm), ttm_eps=str(eps),
                     pe=str(D(v["price"]) / eps),
                     a_price_equivalent_cap=str(D(v["price"]) * D(v["shares"])),
                     ocf_parent_profit_pct=str(D(v["half_ocf"]) / D(v["half_parent_profit"]) * 100))
    commands = [
        ["verify-valuation", "--price", v["price"], "--eps", str(eps)],
        ["verify-market-cap", "--price", v["price"], "--shares", v["shares"],
         "--reported", {"haier": "198160000000", "cosco": "251300000000", "sugar": "42349000000"}[name], "--currency", "CNY"],
    ]
    for command in commands:
        r = subprocess.run([sys.executable, str(ROOT / "tools/financial_rigor.py"), *command],
                           capture_output=True, text=True, check=True)
        logs.append(name + "\n" + r.stdout)

out["lindsay"] = {
    "ocf_net_profit_9m_pct": str(D("30626") / D("44389") * 100),
    "liabilities_pct": str((D("821643") - D("499096")) / D("821643") * 100),
    "pe_at_sep8_close": str(D("123.14") / D("5.20")),
    "estimated_cap_usd": str(D("123.14") * D("10170000")),
    "fcf_9m_usd_million": str((D("30626") - D("35514")) / 1000),
}
out["haier_hvac_revenue_pct"] = str(D("44753572533.34") / D("152115050237.63") * 100)
out["haier_hvac_growth_pct"] = str((D("44753572533.34") / D("42341311688.72") - 1) * 100)
out["haier_buy_range"] = [str(D("1.8") * 10), str(D("2.1") * 10)]
out["haier_fair_range"] = [str(D("1.8") * 12), str(D("2.1") * 12)]
out["haier_stress"] = str(D("1.5") * 8)
out["cosco_buy_range"] = [str(D("15.31") * D("0.8")), str(D("1.4") * 10)]
out["cosco_fair_range"] = [str(D("1.4") * 10), str(D("1.75") * 10)]
out["cosco_stress"] = str(D("0.8") * 8)
out["lindsay_watch_range"] = [str(D("5.2") * 18), str(D("5.2") * 20)]
out["lindsay_stress"] = str(D("3.5") * 15)

cross = [
    ("海尔2026H1归母", {"公告": "103.1625494626", "东方财富": "103.16"}),
    ("海尔2026H1经营现金流", {"公告": "97.5203397771", "东方财富": "97.52"}),
    ("中远2026H1归母", {"公告": "134.189207774", "东方财富": "134.19"}),
    ("中远2026H1经营现金流", {"公告": "233.3022572657", "东方财富": "233.3"}),
    ("LNN2026Q3资产", {"公司新闻稿": "821.643", "StockAnalysis": "821.64"}),
    ("LNN2026Q3权益", {"公司新闻稿": "499.096", "StockAnalysis": "499.1"}),
]
for field, values in cross:
    r = subprocess.run([sys.executable, str(ROOT / "tools/financial_rigor.py"),
                        "cross-validate", "--field", field, "--values", json.dumps(values),
                        "--unit", "亿元或百万美元（见字段）"], capture_output=True, text=True, check=True)
    logs.append(r.stdout)

dest = Path(__file__).with_name("el-nino-funnel-20260910-calculations.json")
dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
Path(__file__).with_name("el-nino-funnel-20260910-validation.txt").write_text("\n".join(logs), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
