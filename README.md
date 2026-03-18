# 🚀 AI Forex Trading Tool (Kenya Edition)

A high-performance, AI-driven Forex trading bot optimized for **EGM Securities** and integrated with **M-Pesa** for autonomous deposits and hyper-growth trading.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FGesi12340%2Fforex-tool&root-directory=frontend)

**Premium Dashboard**: [https://forex-tool-6zbw.vercel.app](https://forex-tool-6zbw.vercel.app)
**Custom Domain**: [https://tool.forex](https://tool.forex)

## 🌟 New Premium Features (V3.2)
- **AI Moonshot Strategy**: Enhanced trend detection (99% confidence threshold) for aggressive 10x-50x growth.
- **Low-Latency Cloud Relay**: Instant synchronization between web and local bot (no ngrok required).
- **Automated M-Pesa (Till/Paybill)**: Fully asynchronous STK Push and B2C withdrawals with zero manual intervention.
- **Zero-Loss Protection**: Dynamic trailing stops and EMA-based "Stop-on-Dip" logic to protect your capital.
- **Premium UI**: Modern dark-mode dashboard with live market tracking and real-time PnL.

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
The dashboard and the local bot are securely connected via a **Cloud Relay**. NO ngrok or manual tunnel configuration is required.
As long as you start the bot (`python backend/api.py`), your dashboard will automatically sync and can control your local bot.

---
**Developed by Gesi12340**
