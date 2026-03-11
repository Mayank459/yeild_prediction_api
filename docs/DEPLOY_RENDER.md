# 🚀 Deploy to Render

This guide will help you deploy the KhetBuddy Yield Prediction API to Render's free tier.

## Prerequisites

- GitHub account (✅ already done)
- Render account (free): https://render.com

## Deployment Steps

### 1. Sign Up / Log In to Render

1. Go to https://render.com
2. Sign up with your GitHub account (recommended)

### 2. Create New Web Service

1. Click **"New +"** button in dashboard
2. Select **"Web Service"**
3. Connect your GitHub repository: `Mayank459/yeild_prediction_api`
4. Render will automatically detect the `render.yaml` file

### 3. Configure Environment Variables

Render will use the configuration from `render.yaml`, but you need to add your OpenWeatherMap API key:

1. In the Render dashboard, go to your service
2. Navigate to **"Environment"** tab
3. Add environment variable:
   - **Key**: `OPENWEATHER_API_KEY`
   - **Value**: Your OpenWeatherMap API key (get from https://openweathermap.org/api)
4. Click **"Save Changes"**

### 4. Deploy

1. Render will automatically start building and deploying
2. Build process takes ~3-5 minutes
3. Once complete, you'll get a live URL like: `https://khetbuddy-api.onrender.com`

## Your API Endpoints

After deployment, your API will be available at:

- **Base URL**: `https://your-app-name.onrender.com`
- **Health Check**: `https://your-app-name.onrender.com/health`
- **API Docs**: `https://your-app-name.onrender.com/docs`
- **Prediction**: `https://your-app-name.onrender.com/api/predict`

## Testing Deployed API

```bash
# Health check
curl https://your-app-name.onrender.com/health

# Get crops
curl https://your-app-name.onrender.com/api/crops

# Predict yield
curl -X POST https://your-app-name.onrender.com/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "crop_type": "Wheat",
    "season": "Rabi",
    "district": "Ludhiana",
    "nitrogen": 80,
    "phosphorus": 40,
    "potassium": 40,
    "soil_ph": 7.0,
    "soil_moisture": 25,
    "irrigation_type": "Canal"
  }'
```

## Render Free Tier Notes

✅ **Free tier includes:**
- 750 hours/month (enough for continuous running)
- Automatic HTTPS
- Automatic deployments from GitHub
- Custom domains (optional)

⚠️ **Limitations:**
- Service spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds (cold start)
- 512 MB RAM limit

## Automatic Deployments

Once set up, Render automatically redeploys when you push to GitHub:

```bash
# Make changes locally
git add .
git commit -m "Update API"
git push origin main

# Render automatically detects and redeploys
```

## Adding Your ML Model

To deploy with a trained model:

1. Add your trained model files:
   ```bash
   mkdir models
   # Add your model.pkl and encoders.pkl
   ```

2. Commit and push:
   ```bash
   git add models/
   git commit -m "Add trained ML model"
   git push origin main
   ```

3. Render will automatically redeploy with the model

## Troubleshooting

### Build Fails
- Check build logs in Render dashboard
- Verify `requirements.txt` has all dependencies

### API Not Responding
- Check if service is running in dashboard
- Free tier spins down after inactivity (30s cold start)

### Environment Variables
- Ensure `OPENWEATHER_API_KEY` is set
- Check Environment tab in Render dashboard

## Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com

---

**That's it!** Your API will be live on the internet with automatic deployments from GitHub. 🎉
