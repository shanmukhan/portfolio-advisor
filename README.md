# Zerodha Long-Term Portfolio Advisor

Direct browser access uses **Investing** at <https://shanmukhan.com/#investing>,
then **Portfolio Advisor**. Sign in with existing RPi Monitor credentials. See
[public hosting and recovery](docs/raspberry-pi.md); the service remains on loopback
with persistent private state and the existing demo/live distinction.

Raspberry Pi service deployment is provided by the sibling Agentic Trader
[shared installer and runbook](../agentic-trader/docs/raspberry-pi.md).
See [Pi usage](docs/raspberry-pi.md) for port 8501, SSH access, mobile monitoring,
persistent state, private credential renewal and recovery. The service starts in
demo mode; this deployment does not import your workstation database or credentials.


A quantitative, multi-factor decision-support dashboard for Indian equities (NSE) engineered for **long-term wealth generation** (1–5+ year compounding horizon). It analyzes your Zerodha portfolio and provides objective **BUY**, **HOLD**, and **SELL** recommendations with transparent rationale, interactive charts, and a disciplined ₹50,000 gross monthly purchase budget framework.

---

## ✨ Features & What Is Included

### 1. Multi-Factor Long-Term Decision Engine
- **🟢 BUY / ACCUMULATE**:
  - High Quality (ROE ≥ 15–20%, low debt, positive cash flow).
  - Margin of safety (P/E at or below Fair P/E).
  - Strong long-term trend (Price above 200-day Simple Moving Average).
- **🟡 HOLD / COMPOUND**:
  - Fundamentals intact, business continues to compound, trading within fair value band.
  - Minimizes friction (taxes, STT, brokerage) by letting compounders run.
- **🔴 SELL / PROFIT-TAKING & THESIS-BREAK PROTECTION**:
  - **Valuation Bubble**: P/E ≥ 1.7x Fair P/E. Locks in accumulated gains (e.g., trim 50%) before multiple compression strikes.
  - **Fundamental Thesis Break**: Severe earnings deceleration (< -10%), surging debt, or negative cash flow. Eliminates value traps.
  - **Severe Trend Breakdown**: Price > 15–20% below 200 SMA with weak fundamentals. Protects accumulated capital.
- **🏦 Dedicated Indian Banking & Financials Model**:
  - Evaluates banks (HDFCBANK, ICICIBANK, SBIN, etc.) and NBFCs using ROE, asset health, and earnings sustainability instead of penalizing standard deposit leverage.

### 2. Modern Fintech UI & Interactive Graphs
- **Portfolio Overview**:
  - Real-time KPI Metric cards (Market Value, Total Unrealized P&L, Monthly Budget, Signal Counts).
  - Interactive **Sector & Asset Allocation Donut Chart**.
  - Color-coded **Holdings Profit & Loss Bar Chart** (Gainers vs. Losers).
  - Detailed holdings table with Avg Buy Price, LTP, P&L (₹ and %), Portfolio Weight, and Advisor Signals.
- **Actionable Recommendations**:
  - Filterable by BUY, HOLD, and SELL with detailed thesis breakdown and suggested actions.
- **Stock Research Studio**:
  - 252+ day interactive **Price Candlestick / Area Chart** with **200-Day SMA** (Trend Anchor) and **50-Day SMA**.
  - **Multidimensional Factor Scorecard Radar Chart** (Quality, Valuation, Growth, Technical, Health).
  - Fundamental ratios grid and long-term thesis & risk diagnostics.
- **Discovery Screener**:
  - Screens curated NSE opportunities not currently held in your portfolio.
  - Risk vs. Momentum Matrix (52-Week Max Drawdown vs. 6-Month Return scatter plot).
- **Monthly Budget & Execution Planner**:
  - Visual gauge for the ₹50,000 monthly purchase cap (IST calendar month).
  - Optimized proposed buy orders honoring max 10% stock and 25% sector concentration limits.
  - Capital harvesting: calculates gross proceeds liberated from SELL recommendations for reinvestment.
  - Transaction ledger: record, view, and delete monthly purchase entries.
- **Zerodha Portfolio Import**:
  - Drag-and-drop CSV export directly from Zerodha Kite / Console (`Instrument, Qty, Avg cost, LTP...`).
  - Manual holding editor (Add / Update custom stocks).
  - Kite Connect Live API configuration status.

---

## 🚀 Quickstart & Installation

```bash
# 1. Clone repository and navigate
cd portfolio-advisor

# 2. Set up virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'

# 3. Create .env configuration
cp .env.example .env

# 4. Run the Streamlit Dashboard
streamlit run app.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`.

---

## 🧪 Testing & CLI Commands

Run the comprehensive test suite (all 10 tests):
```bash
pytest -v
```

Generate full JSON research report via CLI:
```bash
python -m advisor.cli report
```

Record an executed buy in the monthly budget ledger:
```bash
python -m advisor.cli record-buy --date 2026-10-22 --symbol INFY --amount 15000
```

---

## 🔌 Zerodha Kite Live Mode (Optional)

1. Obtain a Kite Connect API key and secret from the official developer portal.
2. In `.env`, set:
   ```env
   ADVISOR_MODE=live
   KITE_API_KEY=your_kite_api_key
   KITE_ACCESS_TOKEN=your_access_token
   ```
3. Update `data/universe.csv` with the NSE symbols you wish to monitor.
4. Run `streamlit run app.py`.

*Note: For security and compliance, the Kite adapter is strictly **read-only** (`holdings`, `instruments`, `historical`, `ltp`, `trades`). It contains zero order execution or write capabilities.*

---

## 📁 Repository Structure

```
portfolio-advisor/
├── advisor/
│   ├── analysis.py        # Technical (200 SMA, 50 SMA) and multi-factor fundamental analysis
│   ├── broker.py          # Read-only Zerodha Kite Connect adapter
│   ├── charts.py          # Plotly visualization modules (Donut, Radar, Candlestick, P&L)
│   ├── cli.py             # Command line interface for reporting and budget recording
│   ├── config.py          # Settings and parameters
│   ├── data.py            # Data loading, demo mode and live Kite synchronization
│   ├── engine.py          # Core portfolio evaluation, P&L aggregation and report generation
│   ├── portfolio.py       # Rebalancing planner for ₹50k monthly budget and sell harvesting
│   └── storage.py         # SQLite persistence for purchases, reports and custom holdings
├── data/
│   ├── demo_fundamentals.csv  # Fundamental data for tracked NSE equities
│   ├── demo_holdings.csv      # Sample Zerodha portfolio holdings
│   ├── universe.csv           # Tracked NSE symbol universe
│   └── prices/                # Daily price history series (252+ trading bars)
├── scripts/
│   ├── generate_sample_data.py # Realistic Indian stock market data generator
│   ├── enrich_user_portfolio.py # Syncs local database holdings with fundamental universe
│   └── login.py               # Interactive Zerodha login & portfolio sync assistant
├── tests/
│   ├── conftest.py            # Shared test fixtures and mock datasets
│   └── test_core.py           # Unit test suite
├── .github/workflows/         # GitHub Actions CI/CD workflows
├── docs/                      # Project analysis and documentation
├── app.py                     # Streamlit web dashboard
├── pyproject.toml             # Dependencies and project metadata
├── requirements.lock          # Pinned dependency lockfile
├── CONTRIBUTING.md            # Developer contribution guidelines
├── CHANGELOG.md               # Version and change history
└── README.md                  # Project documentation
```

---

## ⚠️ Important Disclaimer & Limitations

- **Research Decision Support Only**: Recommendations are algorithmic research hypotheses, not SEBI-registered personalized investment advice.
- **No Order Placement**: This system does not place broker orders or execute financial transactions automatically.
- **Fundamental Data Verification**: Fundamental multiples (P/E, ROE, D/E) should be periodically cross-referenced against official annual reports and quarterly exchange filings.
