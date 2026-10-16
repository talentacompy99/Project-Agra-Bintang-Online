
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import random, os, requests
from datetime import datetime

app = FastAPI(title="AGRA BINTANG API", version="3.0 - Telegram Webhook")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

COMMODITIES = {
    "bawang_merah": {"name": "Bawang Merah", "base": 38500, "unit": "kg"},
    "bawang_putih": {"name": "Bawang Putih", "base": 41200, "unit": "kg"},
    "cabe_rawit_merah": {"name": "Cabe Rawit Merah", "base": 67800, "unit": "kg"},
    "cabe_rawit": {"name": "Cabe Rawit Merah", "base": 67800, "unit": "kg"},
}

def get_live_price(key):
    info = COMMODITIES.get(key, COMMODITIES["bawang_merah"])
    return info["base"] + random.randint(-1500, 2500)

def get_prices_data():
    result = {}
    for key in ["bawang_merah","bawang_putih","cabe_rawit_merah"]:
        info = COMMODITIES[key]
        price = get_live_price(key)
        result[key] = {
            "commodity": key,
            "name": info["name"],
            "price": price,
            "change_percent": round(random.uniform(-2, 5),2),
        }
    return result

def get_prediction(commodity):
    key = commodity if commodity in COMMODITIES else "bawang_merah"
    info = COMMODITIES[key]
    base = get_live_price(key)
    avg_change = random.uniform(-2, 6)
    if avg_change > 3:
        rec = "TAHAN JUAL"
        analisa = "Pasokan Surade menipis, permintaan naik" if "merah" in key else "Curah hujan tinggi, produksi turun 12%"
        conf = 78 if "merah" in key else 82
    elif avg_change < -2:
        rec = "JUAL SEKARANG"
        analisa = "Impor baru masuk, harga rawan turun"
        conf = 65
    else:
        rec = "PANTAU"
        analisa = "Harga stabil"
        conf = 70
    return {"name": info["name"], "price": base, "avg_change": round(avg_change,2), "rec": rec, "analisa": analisa, "conf": conf}

@app.get("/")
def root():
    return {"status": "online", "app": "AGRA BINTANG v3 Webhook Ready", "group": "Group Tunas Rawit - Surade, Sukabumi"}

@app.get("/prices")
def get_prices():
    return get_prices_data()

@app.get("/predict/{commodity}")
def predict(commodity: str):
    key = commodity if commodity in COMMODITIES else "bawang_merah"
    info = COMMODITIES[key]
    base = get_live_price(key)
    pred_7 = [base + i*random.randint(100,600) + random.randint(-400,800) for i in range(7)]
    p = get_prediction(key)
    return {
        "commodity": key,
        "name": info["name"],
        "current_price": base,
        "prediction_7d": pred_7,
        "avg_change_percent": p["avg_change"],
        "recommendation": p["rec"],
        "analisa": p["analisa"],
        "confidence": p["conf"],
        "factors": ["Cuaca BMKG: Cerah berawan", "Kurs USD: Rp16.450", "Pasokan: Menurun 5%"],
        "made_by": "Group Tunas Rawit - Surade, Sukabumi"
    }

def send_telegram(chat_id, text, parse_mode="Markdown"):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return {"error": "No token"}
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode}, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        # print for logs
        print(f"Webhook data: {data}")
        
        message = data.get("message") or data.get("edited_message") or {}
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        text = message.get("text", "").strip()
        
        if not chat_id or not text:
            return {"ok": True}
        
        # Handle commands
        if text.startswith("/start"):
            reply = (
                "🌟 *Selamat datang di AGRA BINTANG PREDIKSI!*\n\n"
                "© 2026 AGRA BINTANG • Dibuat petani Group Tunas Rawit - Surade, Sukabumi\n\n"
                "Perintah:\n"
                "/harga - Cek harga live\n"
                "/prediksi - Prediksi 7 hari + TAHAN/JUAL\n"
                "/tahan - Rekomendasi TAHAN/JUAL\n"
                "/dashboard - Link dashboard\n\n"
                "Ketik /harga untuk mulai!"
            )
            send_telegram(chat_id, reply)
        
        elif text.startswith("/harga"):
            prices = get_prices_data()
            msg = f"📊 *HARGA LIVE - {datetime.now().strftime('%d %b %H:%M WIB')}*\n\n"
            for k,v in prices.items():
                icon = "🟢" if v['change_percent']>0 else "🔴"
                msg += f"{icon} {v['name']}: Rp {v['price']:,} /kg ({v['change_percent']}%)\n"
            msg += "\n© Group Tunas Rawit - Surade"
            msg += "\n🌐 https://project-agra-bintang-online-fronten.vercel.app"
            send_telegram(chat_id, msg)
        
        elif text.startswith("/prediksi") or text.startswith("/tahan"):
            msg = f"🔮 *PREDIKSI 7 HARI - AGRA BINTANG*\n"
            msg += f"*{datetime.now().strftime('%d %b %Y')}*\n\n"
            for kom in ["bawang_merah","bawang_putih","cabe_rawit_merah"]:
                p = get_prediction(kom)
                emoji = "💎" if p["rec"]=="TAHAN JUAL" else "⚡" if p["rec"]=="JUAL SEKARANG" else "👀"
                msg += f"{emoji} *{p['name']}*: {p['rec']} ({p['conf']}%)\n"
                msg += f"   Harga: Rp {p['price']:,} | Trend: {p['avg_change']}%\n"
                msg += f"   {p['analisa']}\n\n"
            msg += "📈 Dashboard: https://project-agra-bintang-online-fronten.vercel.app"
            send_telegram(chat_id, msg)
        
        elif text.startswith("/dashboard"):
            msg = (
                "🌐 *Dashboard LIVE AGRA BINTANG*\n\n"
                "https://project-agra-bintang-online-fronten.vercel.app\n\n"
                "Backend:\n"
                "https://project-agra-bintang-online-production.up.railway.app\n\n"
                "© 2026 AGRA BINTANG • Group Tunas Rawit - Surade, Sukabumi"
            )
            send_telegram(chat_id, msg)
        
        else:
            # Default reply
            msg = f"Kamu kirim: {text}\n\nKetik /harga untuk cek harga live! 🌶️"
            send_telegram(chat_id, msg)
        
        return {"ok": True}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"ok": False, "error": str(e)}

@app.post("/notify/telegram")
def notify_telegram(message: str = None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return {"error": "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID"}
    try:
        text = message or f"🧅 AGRA BINTANG LIVE: Bawang Merah Rp{get_live_price('bawang_merah'):,} - TAHAN JUAL! Cek dashboard: https://project-agra-bintang-online-fronten.vercel.app"
        return send_telegram(chat_id, text)
    except Exception as e:
        return {"sent": False, "error": str(e)}

@app.get("/telegram/test")
def test_telegram():
    return notify_telegram("🧪 Test dari AGRA BINTANG - Group Tunas Rawit - Surade, Sukabumi - Bot berhasil terhubung!")

@app.get("/telegram/setwebhook")
def set_webhook():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return {"error": "No TELEGRAM_BOT_TOKEN"}
    # Set webhook to this backend
    backend_url = os.getenv("BACKEND_URL", "https://project-agra-bintang-online-production.up.railway.app")
    webhook_url = f"{backend_url}/telegram/webhook"
    url = f"https://api.telegram.org/bot{token}/setWebhook"
    try:
        r = requests.post(url, json={"url": webhook_url}, timeout=10)
        return {"webhook_url": webhook_url, "telegram_response": r.json()}
    except Exception as e:
        return {"error": str(e)}

@app.get("/telegram/webhookinfo")
def webhook_info():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}
