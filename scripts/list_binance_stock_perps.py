"""
List all Binance stock/ETF perpetual contracts (non-crypto).
"""
import ccxt, json, sys
sys.stdout.reconfigure(encoding='utf-8')

binance = ccxt.binance({'enableRateLimit': True, 'timeout': 30000})
binance.session.proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}

markets = binance.load_markets()

# All USDT-margined linear perpetuals
stock_perps = {}
for k, v in markets.items():
    if v.get('type') == 'swap' and v.get('linear') and v.get('settle') == 'USDT':
        sym = k.replace('/USDT:USDT', '')
        stock_perps[sym] = k

# Load known crypto list
with open('data/binance_stock_perps.json', 'r') as f:
    crypto_list = json.load(f)

# crypto_list has ALL perps including stocks. We need to filter to only stock/ETF tickers.
# Stock/ETF perps typically have tickers matching real stock symbols (1-5 uppercase letters)
# that aren't in known crypto blacklist.
known_crypto_blacklist = {line.strip() for line in """
BTC ETH BNB XRP ADA SOL DOGE DOT AVAX MATIC LINK UNI SHIB LTC ATOM ETC XLM FIL
TRX ALGO VET ICP SAND MANA EGLD AXS NEAR FLOW APE GMT OP ARB APT SUI PEPE WIF
BONK FLOKI ORDI ENA ETHFI JUP JTO PYTH STRK W ZK NOT IO ZRO LISTA BANANA TON
CAT DOGS POL HMSTR EIGEN SCR KAIA ACX MOVE ME BERA LAYER IP KAITO BMT PAIN
SHELL GPS NIL PARTI GUN USDC USDT FDUSD TUSD DAI USTC BUSD WBTC WETH STETH
EUR TRY BRL PLN RON ARS UAH ZAR COP AAVE ACE ACH ACT AI AERO AGIX ALICE ALPHA
ANKR AR ARKM ASTR ATA AUCTION AVA AXS BABY BAKE BAL BAND BAT BCH BEAM BEAMX
BICO BLUR BLZ BOME BOND BSV CAKE CELO CELR CFX CHZ COMP COTI CRV CTK CTSI CVC
CVX DAR DASH DENT DEXE DGB DIA DYDX DYM EDU ENJ ENS EOS ETC FET FIDA FIL FIO
FLM FLOKI FLOW FLUX FOR FORTH FTM FTT FUN FXS GALA GAS GHST GLM GLMR GMT GMX
GNO GNS GNT GRT GTC HBAR HIGH HNT HOOK HOT ICX ID ILV IMX INJ IOST IOTA IOTX
JASMY JOE JST KAS KAVA KDA KLAY KNC KSM LD0 LDO LINA LINK LIT LOOM LPT LQTY
LRC LSK LTC LUNA LUNC MAGIC MANA MANTA MASK MAV MDT MEME METIS MINA MIOTA MKR
MLN MTL NEO NKN NMR NT NULS OCEAN OGN OM OMG OMNI ONE ONG ONT ORBS ORDI ORN OSMO
OXT PAXG PENDLE PEOPLE PEPE PERP PHA POL POLY POLYX POWR PROM PUNDIX PYR QKC
QNT QTUM RAD RARE REEF REN RENDER REQ RIF RLC RLY RNDR ROSE RPL RSR RUNE RVN
SAFE SAND SC SCRT SEI SFP SKL SLP SNX SNT SOL SPELL SRM STG STMX STORJ STPT
STRAX STX SUN SUSHI SXP SYN SYS T TAKI TAMA TFUEL THETA TIA TLM TON TRAC TRB
TRIBE TRU TRX TUSD TVK UMA UNFI USDP USDC USDT UTK VELO VET VGX VITE VOXEL
VRA VTHO WAN WAVES WAXP WEMIX WIN WLD WLUNA WOO WTC XAI XAUT XCH XCN XDC XEC
XEM XHV XMR XNO XPRT XRD XRP XTZ XVG XVS XYO YFI YGG ZEC ZEN ZIL ZK ZRX
USDC USDT BUSD TUSD DAI FDUSD
""".split()}

# Also filter out things that look like crypto
def looks_like_stock(sym):
    # stocks: 1-5 uppercase letters, no digits unless it's BRK-B etc
    if sym in known_crypto_blacklist:
        return False
    # Allow stock-like names (1-5 uppercase alpha chars)
    if sym.isalpha() and 1 <= len(sym) <= 5 and sym == sym.upper():
        return True
    # Allow tickers with dash like BRK-B
    if all(c.isalpha() or c == '-' for c in sym) and sym == sym.upper():
        return True
    return False

stock_only = {sym: mid for sym, mid in sorted(stock_perps.items()) if looks_like_stock(sym)}

print(f'Stock/ETF perpetuals found: {len(stock_only)}')
print()
for sym, mid in sorted(stock_only.items()):
    print(f'  {sym:8s}  {mid}')

print(f'\n--- Total: {len(stock_only)} stock perpetuals ---')

# Save clean list
with open('data/binance_stock_perps_clean.json', 'w') as f:
    json.dump(sorted(stock_only.keys()), f, indent=2)
print('Saved to data/binance_stock_perps_clean.json')
