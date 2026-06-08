"""
Fetch Binance stock perp data and integrate with DSA analysis.
Run: python scripts/fetch_binance_perps.py
"""
import ccxt, json, sys, os
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

# ─── Binance 美股合约完整列表 ───
STOCK_PERPS = [
    # 科技七巨头
    'AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT', 'NVDA', 'TSLA',
    # 半导体
    'AMD', 'AMAT', 'ARM', 'AVGO', 'INTC', 'MRVL', 'QCOM', 'TSM',
    'AAOI', 'AXTI', 'COHR', 'LITE', 'SNDK', 'WDC', 'MU',
    # 软件/SaaS
    'CRM', 'NOW', 'PLTR', 'ORCL', 'IBM', 'DELL', 'HPE',
    # 金融科技
    'COIN', 'HOOD', 'MSTR', 'SQ',
    # 其他蓝筹
    'BRKB', 'DIS', 'HD', 'JPM', 'V', 'WMT', 'CSCO', 'UBER',
    'LLY', 'NVO', 'NOK', 'BB', 'BABA',
    # AI/云计算
    'CRWV', 'CRDO', 'NBIS', 'IREN', 'RKLB',
    # 太空/新兴
    'ASTS', 'ONDS', 'FLNC',
    # ETF
    'SPY', 'QQQ', 'EWY', 'EWJ', 'EWT', 'SOXL', 'DRAM', 'IWM', 'SPX',
]

binance = ccxt.binance({'enableRateLimit': True, 'timeout': 30000})
binance.session.proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}

print(f'{"SYMBOL":<8s} {"PRICE":>10s} {"24H%":>8s} {"VOL(M)":>10s} {"OI(M)":>10s} {"FUND%":>9s} {"LEV":>4s}')
print('-' * 75)

results = []
errors = []

for sym in STOCK_PERPS:
    market_id = f'{sym}/USDT:USDT'
    try:
        t = binance.fetch_ticker(market_id)
        fr = binance.fetch_funding_rate(market_id)
    except Exception as e:
        errors.append(sym)
        continue

    price = t.get('last') or 0
    chg = t.get('percentage') or 0
    vol = (t.get('quoteVolume') or 0) / 1e6
    oi = float((t.get('info') or {}).get('openInterest', 0))
    oi_usd = oi * price / 1e6 if oi and price else 0
    fund_pct = (fr.get('fundingRate') or 0) * 100
    info = t.get('info') or {}
    lev = info.get('maxLeverage', info.get('leverage', '?'))

    print(f'{sym:<8s} {price:>10.2f} {chg:>+7.2f}% {vol:>10.1f} {oi_usd:>10.1f} {fund_pct:>+8.4f}% {str(lev):>4s}')
    results.append({
        'symbol': sym, 'price': price, 'change_pct': round(chg, 2),
        'volume_24h_m': round(vol, 1), 'open_interest_m': round(oi_usd, 1),
        'funding_rate_pct': round(fund_pct, 4), 'leverage': str(lev),
        'timestamp': datetime.now().isoformat()
    })

print(f'\n--- {len(results)} contracts fetched, {len(errors)} errors ---')
if errors:
    print(f'Not found: {errors}')

os.makedirs('data', exist_ok=True)
with open('data/binance_perp_snapshot.json', 'w') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print('Saved to data/binance_perp_snapshot.json')
