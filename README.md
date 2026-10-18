# Crypto Signals Project
This project analyzes indicators like RSI, MFI, and MACD.

## Crypto Cosmos (`web/crypto-cosmos.html`)
A 3D animation of the Binance market as a solar system, in Arabic. Bitcoin is the sun and the next ten coins orbit it; each planet glows green or red with its 24h change and pulses on every price move. Tap a coin to see its RSI 14, MFI 14 and MACD 12/26/9 on the 15m, 1h or 4h candles, plus a simple buy/sell/neutral reading.

Open the file in a browser; it needs no build step. Prices come from Binance's public market data (REST + WebSocket, no API key). Inside claude.ai, where the page cannot reach Binance, it reads the same Binance pairs through the viewer's TradingView connector. When neither is reachable it runs on clearly labelled demo prices.

For learning only, not financial advice.
