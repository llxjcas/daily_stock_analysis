"""Push Binance perp data report to PushPlus (WeChat)."""
import json, os, sys, urllib.request, ssl
from datetime import datetime

PUSHPLUS_TOKEN = os.getenv('PUSHPLUS_TOKEN', '')
if not PUSHPLUS_TOKEN:
    print('PUSHPLUS_TOKEN not set, skipping push')
    sys.exit(0)

with open('data/binance_perp_snapshot.json', 'r') as f:
    data = json.load(f)

now = datetime.now().strftime('%m-%d %H:%M')
lines = [f'Binance Stock Perps {now}', '=' * 35]

groups = {
    'Your Positions': ['MU', 'NVDA'],
    'Mag 7': ['AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT', 'TSLA'],
    'Semis': ['AMD', 'AMAT', 'ARM', 'AVGO', 'INTC', 'MRVL', 'QCOM', 'TSM'],
    'AI Optical': ['AAOI', 'AXTI', 'COHR', 'LITE'],
    'Storage': ['SNDK', 'WDC', 'MU', 'DRAM'],
    'Software': ['CRM', 'NOW', 'PLTR', 'ORCL', 'IBM', 'DELL'],
    'FinTech': ['COIN', 'HOOD', 'MSTR'],
    'ETFs': ['SPY', 'QQQ', 'SOXL', 'EWY', 'EWJ', 'EWT', 'IWM', 'DRAM'],
}

by_sym = {d['symbol']: d for d in data}

for group_name, symbols in groups.items():
    items = []
    for sym in symbols:
        d = by_sym.get(sym)
        if not d:
            continue
        p = d['price']
        chg = d['change_pct']
        fund = d['funding_rate_pct']
        arrow = '+' if chg > 0 else ''
        fstr = ''
        if abs(fund) > 0.02:
            fstr = ' F:{:.3f}%'.format(fund)
        items.append('{}:{:.0f}{}{:+.1f}%{}'.format(sym, p, arrow, chg, fstr))

    if items:
        lines.append('\n[{}]'.format(group_name))
        for i in range(0, len(items), 3):
            lines.append('  '.join(items[i:i+3]))

lines.append('\n[High Funding Alert (>0.05%)]')
hot = [(s, d) for s, d in by_sym.items() if abs(d['funding_rate_pct']) > 0.05]
if hot:
    for sym, d in sorted(hot, key=lambda x: -abs(x[1]['funding_rate_pct'])):
        lines.append('{}: rate{:.4f}% price{:.1f}'.format(sym, d['funding_rate_pct'], d['price']))
else:
    lines.append('None')

lines.append('\nTotal {} stock perps monitored'.format(len(data)))

content = '\n'.join(lines)

payload = json.dumps({
    'token': PUSHPLUS_TOKEN,
    'title': 'Binance Perps {}'.format(now),
    'content': content,
    'template': 'txt',
    'channel': 'wechat'
}).encode()

ctx = ssl.create_default_context()
req = urllib.request.Request(
    'https://www.pushplus.plus/send',
    data=payload,
    headers={'Content-Type': 'application/json'}
)
resp = urllib.request.urlopen(req, timeout=15, context=ctx)
result = json.loads(resp.read().decode())
print('Push result: {}'.format(result))
