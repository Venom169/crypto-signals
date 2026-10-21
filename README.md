# Crypto Signals Project
This project analyzes indicators like RSI, MFI, and MACD.

## Crypto Cosmos (`web/crypto-cosmos.html`)
A 3D animation of the Binance market as a solar system, in Arabic. Bitcoin is the sun and the next ten coins orbit it; each planet glows green or red with its 24h change and pulses on every price move. Tap a coin to see its RSI 14, MFI 14 and MACD 12/26/9 on the 15m, 1h or 4h candles, plus a simple buy/sell/neutral reading.

Open the file in a browser; it needs no build step. Prices come from Binance's public market data (REST + WebSocket, no API key). Inside claude.ai, where the page cannot reach Binance, it reads the same Binance pairs through the viewer's TradingView connector. When neither is reachable it runs on clearly labelled demo prices.

## Crypto Periodic Table (`web/crypto-periodic.html`)
The same live market laid out as a periodic table of 118 "elements", one per Binance USDT coin. The atomic number is the coin's market-cap rank (October 2026; stablecoins, wrapped tokens and gold left out), the color is its family (payments, layer 1, layer 2, DeFi, memes, AI and data, gaming, infrastructure), and each tile flashes green or red as its price moves. The tiles fly between five views: table, heat (tiles rise or sink with their 24h change), sphere, helix and grid. Tap an element for the same RSI / MFI / MACD card; filter by family or search by symbol or name.

It is a single HTML file using CSS 3D (no WebGL) and the same three data sources as Crypto Cosmos.

## Periodic Table of the Elements (`web/periodic-elements.html`)
The real chemistry table on the same CSS 3D engine, in Arabic and fully offline (no market data). 118 elements colored by family, flying between five views: table; states of matter, where a temperature dial from absolute zero to the Sun's surface melts tiles into sloshing liquids and boils them into floating gases; a discovery timeline from antiquity to 2010; sphere; and helix. Tapping an element opens a card with an animated Bohr atom, its electron configuration (Madelung order plus the known exceptions), melting and boiling points, discovery year and a short fact. A quiz hides the names and asks you to find elements by their Arabic name.

For learning only, not financial advice.
