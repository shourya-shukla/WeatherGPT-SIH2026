````markdown
# WeatherGPT — SIH 2026

WeatherGPT is a disaster-management weather intelligence dashboard for India. It combines live weather data from multiple providers with a Gemini-powered conversational weather assistant.

The system provides current weather, 7-day forecasts, NOAA GFS numerical weather predictions, historical climate analysis, weather alerts, and an interactive weather dashboard.

---

## Features

- 🌤️ Live current weather
- 📅 7-day weather forecast
- 🌧️ Rain probability and precipitation information
- 🌪️ NOAA GFS numerical weather prediction
- 📊 Historical weather and climate analysis
- 🚨 Weather alert support
- 📍 City-based geocoding
- 🤖 Gemini-powered WeatherGPT assistant
- 💬 Markdown-formatted AI responses
- 📱 Responsive React dashboard
- 🔎 City/location search
- 🌐 FastAPI backend with interactive API documentation

---

## Tech Stack

### Frontend

- React
- Vite
- JavaScript
- Lucide React
- React Markdown

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic

### Data & AI

- OpenWeather
- Open-Meteo
- NOAA GFS
- Google Gemini API

---

## Project Structure

```text
WeatherGPT/
│
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── models/
│   └── weather.py
│
├── services/
│   ├── ai.py
│   ├── climate.py
│   ├── geocoding.py
│   ├── history.py
│   ├── nwp.py
│   ├── utils.py
│   └── weather.py
│
└── frontend/
    ├── package.json
    ├── package-lock.json
    ├── index.html
    └── src/
        ├── main.jsx
        └── style.css
````

---

# Running Locally

Follow the steps below to run WeatherGPT on your local machine.

## Prerequisites

Make sure you have the following installed:

* Python 3.10 or newer
* Node.js 18 or newer
* npm
* Git

You will also need:

* Google Gemini API key
* OpenWeather API key

---

## 1. Clone the Repository

```bash
git clone https://github.com/Rubix2103/WeatherGPT-SIH2026
cd WeatherGPT
```

Switch to the development branch if required:

```bash
git checkout dev
git pull origin dev
```

---

# 2. Backend Setup

Open a terminal in the project root.

## Create a Virtual Environment

### Windows PowerShell

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell prevents the script from running:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate the environment again:

```powershell
.venv\Scripts\Activate.ps1
```

---

## Install Backend Dependencies

```powershell
pip install -r requirements.txt
```

---

## Configure API Keys

Create a file named `.env` in the root of the project:

```env
GEMINI_API_KEY=your_gemini_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
```

Replace the values with your actual API keys.

### Important

**Never commit `.env` to Git.**

The repository contains `.env.example` as a template:

```env
GEMINI_API_KEY=
OPENWEATHER_API_KEY=
```

Each developer should create their own `.env`.

---

## Start the Backend

From the project root:

```powershell
uvicorn main:app --reload
```

The backend will start at:

```text
http://localhost:8000
```

FastAPI's interactive API documentation is available at:

```text
http://localhost:8000/docs
```

Keep this terminal running.

---

# 3. Frontend Setup

Open a **new terminal**.

Navigate to the frontend:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Start the Vite development server:

```powershell
npm run dev
```

The frontend will normally start at:

```text
http://localhost:5173
```

Keep this terminal running.

---

# 4. Open the Application

Open your browser and go to:

```text
http://localhost:5173
```

Both the backend and frontend must be running:

```text
Backend
http://localhost:8000
        │
        │ API requests
        ▼
Frontend
http://localhost:5173
```

---

# 5. Verify the Backend

Open:

```text
http://localhost:8000/
```

You should receive:

```json
{
  "message": "WeatherGPT API is running"
}
```

You can also open:

```text
http://localhost:8000/docs
```

to test the API using FastAPI's Swagger interface.

---

# API Endpoints

The API uses the `/api/v1` prefix.

### Current Weather

```text
GET /api/v1/weather/current
```

Example:

```text
http://localhost:8000/api/v1/weather/current?location=Lucknow
```

### 7-Day Forecast

```text
GET /api/v1/weather/forecast
```

Example:

```text
http://localhost:8000/api/v1/weather/forecast?location=Lucknow
```

### NOAA GFS / NWP

```text
GET /api/v1/weather/nwp
```

### Weather Alerts

```text
GET /api/v1/weather/alerts
```

### Geocoding

```text
GET /api/v1/location
```

### Historical Weather

```text
GET /api/v1/weather/history
```

### Climate Analysis

```text
GET /api/v1/climate/analyze
```

### WeatherGPT Chat

```text
POST /api/v1/chat
```

---

# Testing

The easiest way to test the backend is through FastAPI's Swagger UI.

Start the backend:

```powershell
uvicorn main:app --reload
```

Then open:

```text
http://localhost:8000/docs
```

Click an endpoint, select **Try it out**, provide the required parameters, and execute the request.

---

# Data Sources

WeatherGPT currently uses:

| Service           | Purpose                               |
| ----------------- | ------------------------------------- |
| OpenWeather       | Current weather and detailed forecast |
| Open-Meteo        | 7-day dashboard forecast              |
| NOAA GFS          | Numerical weather prediction          |
| Google Gemini     | Conversational weather assistant      |
| Geocoding service | City-to-coordinate conversion         |

Weather values displayed by the dashboard are obtained from external weather providers.

NOAA GFS results are numerical model predictions and should not be treated as guaranteed observations.

For operational disaster-management decisions, official IMD bulletins should be consulted.

---

# Architecture

```text
                         ┌─────────────────────┐
                         │   React + Vite       │
                         │     Frontend        │
                         └──────────┬──────────┘
                                    │
                                    │ HTTP / REST
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │      Backend        │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
       │ OpenWeather │       │ Open-Meteo  │       │  NOAA GFS   │
       │   Weather   │       │  Forecast   │       │     NWP     │
       └─────────────┘       └─────────────┘       └─────────────┘
                                    │
                                    ▼
                            ┌─────────────┐
                            │   Gemini    │
                            │ WeatherGPT  │
                            └─────────────┘
```

---

# Git Workflow

The development branch is:

```text
dev
```

Before starting work:

```powershell
git checkout dev
git pull origin dev
```

After making changes:

```powershell
git status
git add .
git commit -m "describe your changes"
git push origin dev
```

Check the repository status with:

```powershell
git status
```

A clean working tree should show:

```text
nothing to commit, working tree clean
```

---

# Files That Must Not Be Committed

The following files/directories are ignored by Git:

```text
.env
.venv/
node_modules/
__pycache__/
*.pyc
```

API keys and other secrets must remain in `.env`.

---

# Troubleshooting

## Backend does not start

Make sure the virtual environment is activated:

```powershell
.venv\Scripts\Activate.ps1
```

Then install dependencies again:

```powershell
pip install -r requirements.txt
```

Start the server:

```powershell
uvicorn main:app --reload
```

---

## Frontend does not start

Go to the frontend directory:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Then:

```powershell
npm run dev
```

---

## Frontend cannot connect to backend

Make sure the FastAPI server is running:

```text
http://localhost:8000
```

and the frontend is running:

```text
http://localhost:5173
```

Check the browser console and FastAPI terminal for errors.

---

## API key errors

Check that `.env` exists in the project root:

```text
WeatherGPT/
├── .env
├── main.py
└── frontend/
```

and contains:

```env
GEMINI_API_KEY=your_key
OPENWEATHER_API_KEY=your_key
```

Restart the FastAPI server after changing `.env`.

---

# SIH 2026

**WeatherGPT — Disaster Management Weather Intelligence**

Built for **Smart India Hackathon 2026**.

````
