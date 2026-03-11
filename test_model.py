"""Quick test script for the trained KhetBuddy ML model."""
import requests
import json

BASE = "http://localhost:8000"

tests = [
    ("Wheat / Rabi / Ludhiana",   {"latitude": 30.9010, "longitude": 75.8573, "crop_type": "Wheat",  "season": "Rabi",   "nitrogen": 80, "phosphorus": 40, "potassium": 40, "soil_ph": 7.0, "soil_moisture": 25, "irrigation_type": "Canal"}),
    ("Rice / Kharif / Amritsar",  {"latitude": 31.634,  "longitude": 74.872,  "crop_type": "Rice",   "season": "Kharif", "nitrogen": 70, "phosphorus": 35, "potassium": 35, "soil_ph": 6.8, "soil_moisture": 30, "irrigation_type": "Canal"}),
    ("Cotton / Kharif / Bathinda",{"latitude": 30.211,  "longitude": 74.944,  "crop_type": "Cotton", "season": "Kharif", "nitrogen": 60, "phosphorus": 30, "potassium": 30, "soil_ph": 7.5, "soil_moisture": 20, "irrigation_type": "Borewell"}),
    ("Maize / Kharif / Patiala",  {"latitude": 30.341,  "longitude": 76.386,  "crop_type": "Maize",  "season": "Kharif", "nitrogen": 75, "phosphorus": 38, "potassium": 38, "soil_ph": 7.2, "soil_moisture": 28, "irrigation_type": "Canal"}),
]

print("\n" + "="*60)
print(" KhetBuddy ML Model — Live Test")
print("="*60)

all_passed = True
for name, payload in tests:
    r = requests.post(f"{BASE}/api/predict", json=payload, timeout=30)
    d = r.json()
    y   = d.get("yield_per_hectare", {})
    loc = d.get("location", {})
    soil = d.get("soil", {})

    status = "✅ PASS" if r.status_code == 200 and y.get("expected") else "❌ FAIL"
    if r.status_code != 200 or not y.get("expected"):
        all_passed = False

    print(f"\n  [{name}]  {status}")
    print(f"    HTTP status   : {r.status_code}")
    print(f"    District      : {loc.get('district', 'N/A')}")
    print(f"    Yield (qtl/ha): {y.get('lower','?')} – {y.get('expected','?')} – {y.get('higher','?')}")
    print(f"    Soil N/P/K    : {soil.get('nitrogen','?')} / {soil.get('phosphorus','?')} / {soil.get('potassium','?')}")
    if r.status_code != 200:
        print(f"    Error         : {d}")

print("\n" + "="*60)
print(f" Overall: {'✅ All tests passed!' if all_passed else '❌ Some tests failed'}")
print("="*60 + "\n")
