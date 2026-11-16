# 🚀 Deploying PotholeVision to Render

This application is pre-configured for **zero-friction deployment on [Render](https://render.com/)**, fully optimized to run within Render's **Free Tier** limits (512MB RAM, 0.1 CPU).

---

## ⚡ Why This Project Builds Fast & Runs Reliably on Render

1. **Lightweight Model:** Uses fine-tuned YOLOv8n weights (**only 6.3 MB**), fitting directly into the Git repository with negligible memory footprint (~120MB during inference).
2. **CPU-Optimized PyTorch Wheel:** `requirements.txt` points to `--extra-index-url https://download.pytorch.org/whl/cpu`. Instead of downloading 3.5GB CUDA packages that time out, the build downloads only ~150MB and finishes in **under 60 seconds**.
3. **Headless OpenCV:** Uses `opencv-python-headless` to eliminate missing X11/OpenGL library errors (`libGL.so.1`) common in slim Linux cloud environments.
4. **Dynamic Port Binding:** Automatically binds to the `$PORT` environment variable provided by Render.
5. **Dedicated Health Check:** `/health` endpoint configured in `render.yaml` for Render zero-downtime deployment verification.

---

## 📋 Option 1: 1-Click Deploy via Render Blueprint (Recommended)

1. **Push your code to GitHub:**
   ```bash
   cd pothole-detector-site
   git init
   git add .
   git commit -m "Initial commit for Render deployment"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```

2. **Deploy on Render:**
   - Log in to [Render Dashboard](https://dashboard.render.com/).
   - Click **Blueprints** on the left menu (or click **New +** &rarr; **Blueprint**).
   - Connect your GitHub repository.
   - Render will detect the `render.yaml` file automatically and fill in:
     - **Service Name:** `pothole-detector-site`
     - **Runtime:** `Python`
     - **Plan:** `Free`
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
     - **Health Check:** `/health`
   - Click **Apply**.
   - Your site will build and go live in about 1–2 minutes at:
     `https://pothole-detector-site.onrender.com`

---

## 🛠️ Option 2: Manual Web Service Setup on Render

If you prefer to configure manually via the Render UI:

1. Go to [Render Dashboard](https://dashboard.render.com/) &rarr; Click **New +** &rarr; **Web Service**.
2. Connect your GitHub repository.
3. Configure the settings:
   | Setting | Value |
   |---|---|
   | **Name** | `pothole-detector-site` (or your preferred name) |
   | **Region** | Oregon (US West) or Frankfurt (EU) |
   | **Branch** | `main` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
   | **Instance Type** | `Free` |
4. Expand **Advanced Settings**:
   - Add Environment Variable:
     - Key: `PYTHON_VERSION`, Value: `3.11.9`
   - Set **Health Check Path** to `/health`.
5. Click **Create Web Service**.

---

## 🐳 Option 3: Deploy with Docker on Render

If you prefer containerized deployment:

1. Click **New +** &rarr; **Web Service** on Render.
2. Select your repository.
3. Choose **Docker** as the runtime (Render will automatically detect the root `Dockerfile`).
4. Select the **Free** plan.
5. Click **Create Web Service**.

---

## 💡 Render Free Tier Best Practices & Tips

- **Cold Starts (Spin Down):** On Render's Free tier, the service spins down after 15 minutes of inactivity. When a new request arrives, it takes ~30–50 seconds to wake up.
- **Keep-Alive (Optional):** You can use a free monitoring service like [UptimeRobot](https://uptimerobot.com/) or [cron-job.org](https://cron-job.org/) to ping your `/health` endpoint every 10–14 minutes to prevent cold starts.
- **Testing the Live API via cURL:**
  ```bash
  # Check health
  curl https://<your-render-subdomain>.onrender.com/health

  # Run inference on an uploaded image
  curl -X POST "https://<your-render-subdomain>.onrender.com/api/detect" \
    -F "file=@road.jpg" \
    -F "conf=0.20"
  ```
