"""External-service clients (yfinance, EDGAR, NewsAPI, RSS).

Agent nodes call into here for any HTTP or third-party data access. Each tool
exposes a typed async function and is the only place that touches the network.
"""
