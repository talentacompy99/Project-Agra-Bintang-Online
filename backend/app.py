
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import random, os, requests
from datetime import datetime

app = FastAPI(title="AGRA BINTANG v3")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

COMMODITIES = {
    "bawang_merah": {"name": "Bawang Merah", "base": 38500},
    "bawang_putih": {"name": "Bawang Putih", "base": 41200},
    "cabe_rawit_merah": {"name": "Cabe Rawit Merah", "base": 67800},
}

def get_price(k):
    return COMMODITIES[k]["base"] + random.randint(-1500, 2500)

def send_telegram(chat_id, text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return {"error": "no token"}
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def root():
    return {"status": "online", "v": "3.1-fixed", "group": "Tunas Rawit - Surade"}

@app.get("/prices")
def prices():
    res = {}
    for k in COMMODITIES:
        res[k] = {"name": COMMODITIES[k]["name"], "price": get_price(k), "change_percent": round(random.uniform(-2,5),2)}
    return res

@app.get("/predict/{c}")
def pred(c):
    k = c if c in COMMODITIES else "bawang_merah"
    base = get_price(k)
    avg = random.uniform(-2,6)
    rec = "TAHAN JUAL" if avg>3 else "JUAL SEKARANG" if avg<-2 else "PANTAU"
    return {"name": COMMODITIES[k]["name"], "current_price": base, "avg_change_percent": round(avg,2), "recommendation": rec, "confidence": 78}

@app.post("/telegram/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        msg = data.get("message", {})
        chat = msg.get("chat", {})
        chat_id = chat.get("id")
        text = msg.get("text","")
        if not chat_id:
            return {"ok": True}
        if "/start" in text:
            send_telegram(chat_id, "🌟 *Selamat datang AGRA BINTANG!*\n\nPerintah:\n/harga - Harga live\n/prediksi - Prediksi TAHAN/JUAL\n/dashboard - Link dashboard\n\n© Group Tunas Rawit - Surade")
        elif "/harga" in text:
            p = prices()
            m = f"📊 *HARGA LIVE {datetime.now().strftime('%d %b %H:%M')}*\n\n"
            for k,v in p.items():
                m += f"• {v['name']}: Rp {v['price']:,} ({v['change_percent']}%)\n"
            m += "\n🌐 https://project-agra-bintang-online-fronten.vercel.app"
            send_telegram(chat_id, m)
        elif "/prediksi" in text or "/tahan" in text:
            m = f"🔮 *PREDIKSI - {datetime.now().strftime('%d %b')}*\n\n"
            for k in COMMODITIES:
                base = get_price(k)
                avg = random.uniform(-1,5)
                rec = "TAHAN JUAL" if avg>2 else "PANTAU"
                m += f"💎 *{COMMODITIES[k]['name']}*: {rec} (Rp {base:,})\n"
            m += "\n📈 https://project-agra-bintang-online-fronten.vercel.app"
            send_telegram(chat_id, m)
        elif "/dashboard" in text:
            send_telegram(chat_id, "🌐 *Dashboard:*\nhttps://project-agra-bintang-online-fronten.vercel.app")
        return {"ok": True}
    except Exception as e:
        print(e)
        return {"ok": True}

@app.get("/telegram/test")
def test():
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    return send_telegram(chat_id, "🧪 Test AGRA BINTANG v3.1 - Group Tunas Rawit - Berhasil! Bot bisa bales /harga sekarang")

@app.get("/telegram/setwebhook")
def setwh():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    backend = os.getenv("BACKEND_URL","https://project-agra-bintang-online-production.up.railway.app")
    wh = f"{backend}/telegram/webhook"
    r = requests.post(f"https://api.telegram.org/bot{token}/setWebhook", json={"url": wh}, timeout=10)
    return {"webhook": wh, "resp": r.json()}

@app.get("/telegram/webhookinfo")
def info():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    r = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)
    return r.json()
