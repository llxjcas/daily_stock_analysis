"""
Fetch Binance stock perp data — Binance only, no external validation.
"""
import ccxt, json, sys, os
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

# 币安美股永续合约（已验证存在）
STOCKS = [
    'AAPL','AMZN','GOOGL','META','MSFT','NVDA','TSLA',
    'AMD','AMAT','ARM','AVGO','INTC','MRVL','QCOM','TSM',
    'AAOI','AXTI','COHR','LITE','SNDK','WDC','MU',
    'CRM','NOW','PLTR','ORCL','IBM','DELL','HPE',
    'COIN','HOOD','MSTR',
    'DIS','HD','JPM','V','WMT','CSCO','UBER',
    'LLY','NVO','NOK','BABA',
    'CRWV','CRDO','NBIS','IREN','RKLB',
    'ASTS','ONDS','FLNC',
    'SPY','QQQ','EWY','EWJ','EWT','SOXL','DRAM','IWM',
]

binance = ccxt.binance({'enableRateLimit': True, 'timeout': 30000})
binance.session.proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}

results = []
print(f'{"代码":<8s} {"价格":>12s} {"24H涨跌":>9s} {"24H量(万)":>12s} {"资金费率":>9s}')
print('-' * 55)

for sym in STOCKS:
    mid = f'{sym}/USDT:USDT'
    try:
        t = binance.fetch_ticker(mid)
        fr = binance.fetch_funding_rate(mid)
    except Exception as e:
        print(f'{sym:<8s} ERROR: {e}')
        continue

    price = t.get('last') or 0
    chg = t.get('percentage') or 0
    vol = int((t.get('quoteVolume') or 0) / 10000)
    fund_pct = (fr.get('fundingRate') or 0) * 100

    print(f'{sym:<8s} {price:>12.2f} {chg:>+8.2f}% {vol:>12,} {fund_pct:>+8.4f}%')
    results.append({
        'symbol': sym, 'price': price, 'change_pct': round(chg, 2),
        'volume_wan': vol, 'funding_rate_pct': round(fund_pct, 4),
        'ts': datetime.now().isoformat()
    })

os.makedirs('data', exist_ok=True)
with open('data/binance_perp_snapshot.json', 'w') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f'\n{len(results)} 只合约 | 数据来源: 币安实时')
