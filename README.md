# 🚀 AI Forex Trading Tool (Kenya Edition)

A high-performance, AI-driven Forex trading bot optimized for **EGM Securities** and integrated with **M-Pesa** for autonomous deposits and hyper-growth trading.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FGesi12340%2Fforex-tool&root-directory=frontend)

**Shareable Link**: [https://forextool.vercel.app](https://forextool.vercel.app)
*(If the link above is not yet active, click the Deploy button once as a one-time setup)*

## 🌟 Features
- **MT5 Integration**: Connects directly to MetaTrader 5 (EGM Securities, FXPesa, etc.).
- **AI Moonshot Strategy**: Dynamic ADX/RSI trend detection for 10x-50x profit targets.
- **Zero-Loss Protection**: Autonomous EMA-based exit logic to protect capital.
- **M-Pesa Integration**: Automated STK Push for seamless account funding.

## 🛠️ Setup for Friends

### 1. The Dashboard (Live Link)
Click the **Deploy to Vercel** button above. Vercel will create a live website link for you (e.g., `forex-tool.vercel.app`).

### 2. The Engine (Your Local PC)
The trading logic must run on a PC with MetaTrader 5 installed.
1. Clone this repo: `git clone https://github.com/Gesi12340/forex-tool.git`
2. Install requirements: `pip install -r backend/requirements.txt`
3. Configure your `.env` file with your credentials.
4. Start the bot: `python backend/api.py`

### 3. Connect the Two
To let the website talk to your local bot, use **ngrok**:
1. Run `ngrok http 5000`.
2. Copy the `https://...` link ngrok gives you.
3. Paste that link into the **Backend Connection** box on your Vercel website.

---
**Developed by Gesi12340**
