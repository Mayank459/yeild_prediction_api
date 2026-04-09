# 🌾 KhetBuddy: Project Architecture & Design Decisions

## 1. What is KhetBuddy?
**KhetBuddy** is an end-to-end Machine Learning system that predicts crop yield (how much a farmer will harvest per hectare) for farmers in Punjab, India. 

The project has two main parts:
1. **The Backend API (FastAPI)**: The brain of the system. It takes in GPS coordinates, auto-fetches real-time weather, soil parameters, and location data, and passes all that to a Machine Learning model to calculate the yield. This is hosted on Render.
2. **The Frontend App (Streamlit)**: A clean, simple web interface where a farmer (or user) drops a pin on a map or types their coordinates, selects their crop, and instantly sees the prediction. This is hosted on Streamlit Community Cloud.

---

## 2. How the System Works (The Data Pipeline)

The core philosophy of KhetBuddy is **minimal user effort**. 

Asking a farmer, *"What is the potassium level of your soil in kg/ha?"* is terrible UX. Instead, KhetBuddy only asks for:
*   **Latitude & Longitude** (GPS Location)
*   **Crop Type** (e.g., Wheat, Rice)
*   **Irrigation Type** (e.g., Canal, Borewell)

Behind the scenes, the API instantly does this:
1.  **Reverse Geocoding (Nominatim API):** Converts the GPS coordinates into a District and State (e.g., Ludhiana, Punjab).
2.  **Weather Fetching (OpenWeatherMap API):** Grabs current temperature, rainfall, and humidity for those exact coordinates.
3.  **Soil Fetching (SoilGrids API & District Averages):** Grabs the Nitrogen, Phosphorus, Potassium, and pH levels based on the GPS coordinates or fallback regional averages.
4.  **Feature Engineering:** Calculates "Nutrient Index" and "Stress Indicators" from the raw weather and soil data.
5.  **ML Prediction:** Feeds all 15 inputs into a pre-trained **Random Forest Regressor** model.
6.  **Response:** Returns the expected yield (quintals/hectare) back to the user's screen.

---

## 3. Why We Used This and Not That (Design Decisions Q&A)

### Q: Why build a FastAPI backend instead of Flask or Django?
*   **Why not Django?** Django is a massive framework designed for building giant, database-heavy websites (like Instagram). We don't have a giant database of users right now; we just need a fast API. Django would be too heavy and slow to boot up.
*   **Why not Flask?** Flask is micro, but **FastAPI** provides automatic data validation (using Pydantic) and automatically generates interactive API Documentation (Swagger UI). In Machine Learning APIs, validating that an incoming number is a float within a specific range is crucial. FastAPI does this effortlessly; Flask requires heavy manual coding.

### Q: Why separate the Streamlit frontend from the FastAPI backend?
*   **Why not put everything in one file?** 
    1.  **Scalability:** If a mobile developer wants to build a KhetBuddy Android app tomorrow, they can't connect to a Streamlit app. By separating the API (FastAPI) from the UI (Streamlit), the API acts as a universal brain. A web app, an Android app, an iOS app, and a smartwatch can all talk to the exact same API.
    2.  **Deployment:** Machine Learning APIs require heavy dependencies (`scikit-learn`, `pandas`). UIs require UI dependencies (`streamlit`). Splitting them means the UI loads blazingly fast on Streamlit Cloud, while the heavy lifting happens on a dedicated API server.

### Q: Why use external APIs (OpenWeatherMap, SoilGrids) instead of downloading a massive database?
*   **Why not a static database?** We *could* download a 50GB file of every inch of soil in India and host it. However:
    1.  Hosting a 50GB database is incredibly expensive and slow to query.
    2.  Weather changes daily. A static database can't predict yield based on *today's* heatwave.
*   **The API Approach:** By calling OpenWeatherMap and SoilGrids on the fly, our backend remains incredibly lightweight (just a few MBs) while always having access to the most up-to-date real-world data across the entire globe.

### Q: Why use a Random Forest model instead of Deep Learning (Neural Networks)?
*   **Why not Deep Learning?** Deep Learning (like TensorFlow/PyTorch) is amazing for recognizing images (computer vision) or generating text (LLMs). But for "Tabular Data" (data that looks like an Excel spreadsheet — temperature, rainfall, nitrogen), tree-based models like **Random Forest** almost always outperform Neural Networks.
*   **The Random Forest Advantage:** It is faster to train, requires significantly less data to become accurate, is less prone to overfitting, and most importantly, it offers **Feature Importance** (it can tell us *why* it made a decision, e.g., "Rainfall was the #1 factor for this crop failure"). Neural networks are usually "black boxes".

### Q: Why use `.pkl` (Pickle/Joblib) files to save the model?
*   **Why not ONNX or PMML?** While ONNX is great for cross-language compatibility (training in Python, running in C++), our entire stack (training and API) is Python. `joblib` is optimized heavily for saving `scikit-learn` models containing large NumPy arrays (which Random Forest trees are made of). It is the fastest and most native way to freeze a Python model and wake it up inside FastAPI.

### Q: Why are all the API inputs marked as "Optional" except GPS and Crop?
*   **Why not force the farmer to enter everything?** Because farmers likely don't know the exact `soil_ph` or `humidity` decimal at their exact location at any given moment. 
*   **The Override Design:** The API is designed to auto-fetch everything gracefully. However, if an Agricultural Scientist comes to the platform and *does* know the exact Nitrogen level because they just tested the soil, they can override the auto-fetched value by providing it. This makes the API idiot-proof for average users, but incredibly powerful for power-users.

### Q: Why do we need these specific 15 inputs? How do they affect yield?
To accurately calculate how much crop will grow, a Machine Learning model needs to understand the plant's environment. We chose these specific inputs because they are the biological building blocks of plant growth:
1.  **Nitrogen, Phosphorus, Potassium (NPK):** The three macronutrients. Nitrogen makes leaves grow (crucial for wheat), Phosphorus develops strong roots, and Potassium guards against disease.
2.  **Soil pH:** If the soil is too acidic (pH < 5) or too alkaline (pH > 8), the plant roots physically cannot absorb the NPK fertilizers, suffocating the plant.
3.  **Soil Moisture:** A measure of how much water the roots are currently holding.
4.  **Temperature & Rainfall:** Different crops have different critical temperature thresholds. For example, if Wheat experiences a sudden heatwave above 30°C during its "grain-filling" stage, the yield drops massively.
5.  **Irrigation Type:** A "Rainfed" crop is completely dependent on the weather. A "Canal" or "Borewell" crop has a buffer against droughts, meaning the model can predict higher yields even in low-rainfall years.
6.  **Crop Type & Season:** The biological baseline. Rabi (Winter) Wheat will yield completely differently than Kharif (Monsoon) Rice.

### Q: Where did we get the historical data to train the model?
A machine learning model is only as good as the data it learned from. We trained the model using decades of real historical data from Punjab:
1.  **Crop Yield Data (`apy.csv`):** We downloaded the official **"India Agriculture Production Statistics"** dataset from **[data.gov.in](https://data.gov.in)**. This dataset contains year-by-year records of exactly how many hectares of Wheat, Rice, Cotton, etc. were planted in every district of Punjab, and exactly how many tonnes were harvested.
2.  **Historical Weather Data:** We mapped the historical crop years to historical temperature and rainfall data from **NASA POWER** (an API providing decades of localized climate records) and official Punjab meteorological reports. 
3.  **Historical Soil Data:** We used the **Indian Soil Health Card baseline data** to understand the average NPK levels of each district over the last decade.
By joining these three datasets together, the Random Forest model learned the *exact math* of how weather and soil impacted real Punjab harvests over the last 20 years.
