"""
Fetch Binance stock perp data validated against Yahoo Finance.
"""
import ccxt, json, sys, os, sqlite3
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

import yfinance as yf

# 候选股票列表（从币安合约中筛选）
CANDIDATES = [
    'AAPL','AMZN','GOOGL','META','MSFT','NVDA','TSLA',
    'AMD','AMAT','ARM','AVGO','INTC','MRVL','QCOM','TSM',
    'AAOI','AXTI','COHR','LITE','SNDK','WDC','MU',
    'CRM','NOW','PLTR','ORCL','IBM','DELL','HPE',
    'COIN','HOOD','MSTR',
    'BRKB','DIS','HD','JPM','V','WMT','CSCO','UBER',
    'LLY','NVO','NOK','BABA',
    'CRWV','CRDO','NBIS','IREN','RKLB',
    'ASTS','ONDS','FLNC',
    'SPY','QQQ','EWY','EWJ','EWT','SOXL','DRAM','IWM',
]

binance = ccxt.binance({'enableRateLimit': True, 'timeout': 30000})
binance.session.proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}

print('验证美股合约真实性...')
print()

# 先用Yahoo Finance批量验证哪些是真正的股票
valid_stocks = []
invalid_stocks = []

for sym in CANDIDATES:
    mid = f'{sym}/USDT:USDT'
    try:
        # 获取币安价格
        bt = binance.fetch_ticker(mid)
        bnb_price = bt.get('last')
        if not bnb_price or bnb_price <= 0:
            invalid_stocks.append((sym, 'no price'))
            continue

        # 获取Yahoo Finance价格对比
        yt = yf.Ticker(sym)
        yf_info = yt.fast_info
        yf_price = getattr(yf_info, 'last_price', None) or getattr(yf_info, 'regular_market_previous_close', None) or getattr(yf_info, 'previous_close', None)

        if yf_price and yf_price > 0:
            diff = abs(bnb_price - yf_price) / yf_price
            if diff < 0.15:  # 偏差<15%的是真股票
                valid_stocks.append(sym)
                print(f'  {sym:6s} ✅ 币安{bnb_price:>10.2f} 雅虎{yf_price:>10.2f} 偏差{diff:.1%}')
            else:
                invalid_stocks.append((sym, 'price mismatch: binance={:.2f} yahoo={:.2f}'.format(bnb_price, yf_price)))
                print(f'  {sym:6s} ❌ 价格不匹配 币安{bnb_price:.2f} 雅虎{yf_price:.2f}')
        else:
            invalid_stocks.append((sym, 'no yahoo data'))
            print(f'  {sym:6s} ⚠️ 雅虎无数据 币安价{bnb_price:.2f}')
    except Exception as e:
        invalid_stocks.append((sym, str(e)[:50]))
        print(f'  {sym:6s} ❌ {e}')

print()
print(f'验证通过: {len(valid_stocks)} 只')
print(f'剔除: {len(invalid_stocks)} 只')
if invalid_stocks:
    for s, r in invalid_stocks:
        print(f'  {s}: {r}')

# 获取验证通过的合约实时数据
print()
print(f'{"代码":<8s} {"价格":>10s} {"24H%":>8s} {"成交量(万)":>10s} {"费率%":>9s}')
print('-' * 55)

results = []
for sym in valid_stocks:
    mid = f'{sym}/USDT:USDT'
    try:
        t = binance.fetch_ticker(mid)
        fr = binance.fetch_funding_rate(mid)
    except:
        continue

    price = t.get('last') or 0
    chg = t.get('percentage') or 0
    vol = int((t.get('quoteVolume') or 0) / 10000)
    fund_pct = (fr.get('fundingRate') or 0) * 100

    print(f'{sym:<8s} {price:>10.2f} {chg:>+7.2f}% {vol:>10,} {fund_pct:>+8.4f}%')
    results.append({
        'symbol': sym, 'price': price, 'change_pct': round(chg, 2),
        'volume_wan': vol, 'funding_rate_pct': round(fund_pct, 4),
        'timestamp': datetime.now().isoformat()
    })

os.makedirs('data', exist_ok=True)
with open('data/binance_perp_snapshot.json', 'w') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f'\n保存 {len(results)} 只验证通过的合约到 data/binance_perp_snapshot.json')
