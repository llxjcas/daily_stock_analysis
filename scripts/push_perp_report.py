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
lines = ['💰 币安美股永续合约 {}'.format(now), '=' * 35]

groups = {
    '🔴 你的持仓': ['MU', 'NVDA'],
    '🟠 科技七巨头': ['AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT', 'TSLA'],
    '🔵 半导体': ['AMD', 'AMAT', 'ARM', 'AVGO', 'INTC', 'MRVL', 'QCOM', 'TSM'],
    '🟣 AI光通信': ['AAOI', 'AXTI', 'COHR', 'LITE'],
    '🟤 存储芯片': ['SNDK', 'WDC', 'MU', 'DRAM'],
    '🟢 软件/SaaS': ['CRM', 'NOW', 'PLTR', 'ORCL', 'IBM', 'DELL'],
    '🟡 金融科技': ['COIN', 'HOOD', 'MSTR'],
    '⚪ 指数ETF': ['SPY', 'QQQ', 'SOXL', 'EWY', 'EWJ', 'EWT', 'IWM', 'DRAM'],
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
            fstr = ' 💰费率{:.3f}%'.format(fund)
        items.append('{} {:.0f}{}{:+.1f}%{}'.format(sym, p, arrow, chg, fstr))

    if items:
        lines.append('\n{}'.format(group_name))
        for i in range(0, len(items), 3):
            lines.append('  '.join(items[i:i+3]))

lines.append('\n🔴 高费率预警 (>0.05%)')
hot = [(s, d) for s, d in by_sym.items() if abs(d['funding_rate_pct']) > 0.05]
if hot:
    for sym, d in sorted(hot, key=lambda x: -abs(x[1]['funding_rate_pct'])):
        lines.append('[{}] 费率{:.4f}% 价{:.1f}'.format(sym, d['funding_rate_pct'], d['price']))
    lines.append('⚠️ 费率>0.05%=多头拥挤 注意回调风险')
else:
    lines.append('✅ 无异常 市场情绪平稳')

lines.append('\n📊 共监控{}只美股合约'.format(len(data)))

content = '\n'.join(lines)

payload = json.dumps({
    'token': PUSHPLUS_TOKEN,
    'title': '💰 币安美股合约 {}'.format(now),
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
