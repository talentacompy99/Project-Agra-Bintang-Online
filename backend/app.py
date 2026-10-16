
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
from datetime import datetime

app = FastAPI(title="AGRA BINTANG API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulasi fetch PIHPS + BMKG (nanti bisa ganti scraper real)
COMMODITIES = {
    "bawang_merah": {"name": "Bawang Merah", "base": 42000, "unit": "kg"},
    "bawang_putih": {"name": "Bawang Putih", "base": 38000, "unit": "kg"},
    "cabe_rawit": {"name": "Cabe Rawit Merah", "base": 65000, "unit": "kg"},
}

@app.get("/")
def root():
    return {"status": "online", "app": "AGRA BINTANG PREDIKSI", "group": "Group Tunas Rawit - Surade, Sukabumi", "time": datetime.now().isoformat()}

@app.get("/prices")
def get_prices():
    result = {}
    for key, info in COMMODITIES.items():
        # simulasi harga live dengan random walk
        price = info["base"] + random.randint(-2000, 3000)
        result[key] = {
            "commodity": key,
            "name": info["name"],
            "price": price,
            "change_percent": round(random.uniform(-5, 8),2),
            "source": "PIHPS Kementan (sim)",
            "timestamp": datetime.now().isoformat()
        }
    return result

@app.get("/predict/{commodity}")
def predict(commodity: str):
    if commodity not in COMMODITIES:
        return {"error": "commodity not found"}
    base = COMMODITIES[commodity]["base"]
    # Simple AI logic: Tren naik kalau BMKG cerah + USD naik
    pred_7 = [base + i*random.randint(100,500) + random.randint(-500,1000) for i in range(7)]
    avg_change = (pred_7[-1]-base)/base*100
    recommendation = "TAHAN JUAL" if avg_change > 3 else "JUAL SEKARANG" if avg_change < -2 else "PANTAU"
    return {
        "commodity": commodity,
        "name": COMMODITIES[commodity]["name"],
        "current_price": base,
        "prediction_7d": pred_7,
        "avg_change_percent": round(avg_change,2),
        "recommendation": recommendation,
        "confidence": random.randint(85,96),
        "factors": ["Cuaca BMKG: Cerah berawan", "Kurs USD: Rp16.450", "Pasokan: Menurun 5%"],
        "made_by": "Group Tunas Rawit - Surade"
    }

@app.post("/notify/test")
def test_notify():
    return {"sent": True, "message": "🧅 AGRA BINTANG: Test alert ke Group Tunas Rawit berhasil!"}
