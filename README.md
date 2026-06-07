
#  Smart Watering System with IoT

An intelligent, low-cost IoT-enabled plant irrigation system that leverages real-time sensor data, cloud analytics, and AI-driven predictions to optimize water usage in agriculture.

## Overview
Drought and water scarcity affect hundreds of millions of people globally. Agriculture accounts for approximately **80% of consumptive water use** in the United States alone. This project leverages IoT, AI, and cloud computing to develop a precision irrigation system that:

- Monitors soil moisture, temperature, humidity, and light intensity in real time
- Uploads sensor data to **ThingSpeak** cloud platform
- Applies **machine learning** to predict irrigation needs
- Automates water pump control or sends smart notifications
- Forecasts seasonal water usage using time-series models
# prototype
<img width="1918" height="776" alt="image" src="https://github.com/user-attachments/assets/c0fb6062-7feb-455b-8bc6-cf9da0d30a22" />
demo:<img width="1913" height="912" alt="image" src="https://github.com/user-attachments/assets/d1c55d30-288f-4454-ae39-06d627a7f1b4" />

# architecture
<img width="846" height="653" alt="image" src="https://github.com/user-attachments/assets/ea439563-e580-4e03-b715-c8e2c536689f" />
[Uploading smart_watering_dashboard.html…]()
# workflow:<img width="967" height="880" alt="image" src="https://github.com/user-attachments/assets/60c7d2d6-9b14-4f2a-a407-f98f5252fdf7" />

## Features

| Feature | Description |
|---|---|
|  Multi-sensor support | Soil moisture, temperature, humidity, light, pH |
|  Cloud integration | ThingSpeak IoT platform for data storage & analytics |
|  AI predictions | ML model to predict watering schedule |
|  Live dashboard | Web-based real-time monitoring dashboard |
|  Smart alerts | Email/SMS notifications for irrigation events |
|  Actuator control | Automatic relay-based pump control |
|  Weather API | OpenWeatherMap integration for forecast-based scheduling |
|  ET estimation | Evapotranspiration calculation (Penman-Monteith method) |

## System Architecture

┌─────────────────────────────────────────────────────────────┐
│                     FIELD / GREENHOUSE                      │
│                                                             │
│  [Soil Moisture]  [DHT22]  [LDR]  [pH Sensor]             │
│        │              │       │         │                   │
│        └──────────────┴───────┴─────────┘                  │
│                         │                                   │
│                   [ESP32 / Arduino]                         │
│                   (Edge Processing)                         │
│                         │                                   │
│              [Relay Module + Water Pump]                    │
└─────────────────────────────────────────────────────────────┘
                          │ WiFi / MQTT
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    CLOUD PLATFORM                           │
│                                                             │
│  ThingSpeak ──► Data Storage & Visualization               │
│      │                                                      │
│      ├──► MATLAB Analytics (ET Estimation, Forecasting)    │
│      └──► Python ML Pipeline (Random Forest / LSTM)        │
│                                                             │
│  OpenWeatherMap ──► Weather Forecast Integration           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    WEB DASHBOARD                            │
│                                                             │
│  Real-time charts │ Irrigation history │ Alerts & Logs     │
└─────────────────────────────────────────────────────────────┘

## Hardware Requirements

| Component | Model | Qty | Approx. Cost |
|---|---|---|---|
| Microcontroller | ESP32 DevKit v1 | 1 | $5–8 |
| Soil Moisture Sensor | Capacitive v1.2 | 2–4 | $2–4 each |
| Temp & Humidity | DHT22 | 1 | $3–5 |
| Light Sensor | LDR / BH1750 | 1 | $1–3 |
| pH Sensor | Analog pH Module | 1 | $8–12 |
| Relay Module | 5V 1-Channel | 1 | $2–3 |
| Water Pump | 5V Mini Submersible | 1 | $3–5 |
| Jumper Wires + Breadboard | — | — | $3–5 |
| Power Supply | 5V USB or Li-Po | 1 | $4–8 |
| **Total** | | | **~$35–60** |

## Software Requirements

- **Arduino IDE** 2.x or PlatformIO
- **Python** 3.9+
- **Node.js** 16+ (for dashboard)
- **ThingSpeak account** (free tier available)
- **OpenWeatherMap API key** (free tier available)
- Python packages: see `requirements.txt`

## Project Structure

smart-watering-iot/
├── src/
│   ├── arduino/
│   │   ├── main.ino                  # Main ESP32 firmware
│   │   ├── sensors.ino               # Sensor reading functions
│   │   ├── wifi_manager.ino          # WiFi + ThingSpeak upload
│   │   └── pump_control.ino          # Relay/pump control logic
│   ├── python/
│   │   ├── data_fetcher.py           # ThingSpeak data retrieval
│   │   ├── weather_api.py            # OpenWeatherMap integration
│   │   ├── et_calculator.py          # Evapotranspiration (Penman-Monteith)
│   │   ├── irrigation_model.py       # ML model for irrigation prediction
│   │   ├── train_model.py            # Model training pipeline
│   │   ├── predict.py                # Inference + trigger logic
│   │   ├── notifier.py               # Email/SMS alerts
│   │   └── scheduler.py              # Cron-based scheduling
│   └── matlab/
│       ├── et_estimation.m           # ET analysis in MATLAB
│       ├── water_forecast.m          # Seasonal water forecasting
│       └── thingspeak_analysis.m     # ThingSpeak MATLAB plugin
├── dashboard/
│   ├── index.html                    # Main dashboard UI
│   ├── css/
│   │   └── styles.css
│   └── js/
│       ├── charts.js                 # Chart.js visualizations
│       └── thingspeak_api.js         # Live data fetching
├── models/
│   ├── irrigation_rf_model.pkl       # Trained Random Forest model
│   └── scaler.pkl                    # Feature scaler
├── config/
│   ├── config.example.yaml           # Configuration template
│   └── crop_parameters.json          # Crop-specific water requirements
├── docs/
│   ├── wiring_diagram.png            # Hardware wiring diagram
│   ├── architecture.png              # System architecture
│   └── setup_guide.md                # Detailed setup instructions
├── tests/
│   ├── test_sensors.py
│   ├── test_et_calculator.py
│   └── test_irrigation_model.py
├── .github/
│   └── workflows/
│       └── ci.yml                    # GitHub Actions CI pipeline
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md

## Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/smart-watering-iot.git
cd smart-watering-iot

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys and channel IDs

### 4. Flash ESP32 Firmware

1. Open `src/arduino/main.ino` in Arduino IDE
2. Install required libraries (see `docs/setup_guide.md`)
3. Update WiFi credentials and ThingSpeak channel key in `main.ino`
4. Select board: **ESP32 Dev Module** → Upload

### 5. Run the Prediction Pipeline

```bash
python src/python/scheduler.py

### 6. Launch the Dashboard

```bash
# Open dashboard/index.html in browser
# Or serve with Python:
python -m http.server 8080 --directory dashboard

## Configuration

Edit `config/config.example.yaml` and rename to `config.yaml`:

```yaml
thingspeak:
  channel_id: "YOUR_CHANNEL_ID"
  read_api_key: "YOUR_READ_KEY"
  write_api_key: "YOUR_WRITE_KEY"

weather:
  api_key: "YOUR_OPENWEATHERMAP_KEY"
  location: "Warangal, IN"
  units: "metric"

irrigation:
  soil_moisture_threshold: 30    # % — water when below this
  pump_duration_seconds: 15
  check_interval_minutes: 30

crop:
  type: "tomato"                 # See crop_parameters.json
  growth_stage: "vegetative"

notifications:
  email: "your@email.com"
  smtp_server: "smtp.gmail.com"
  smtp_port: 587

## Analytics & AI Models

### Evapotranspiration (ET) Estimation

The system uses the **Penman-Monteith** equation to estimate crop water demand:
`
ET₀ = [0.408Δ(Rn - G) + γ(900/(T+273))u₂(es - ea)] / [Δ + γ(1 + 0.34u₂)]
``
Where:
- `Rn` = net radiation, `T` = mean temperature
- `u₂` = wind speed at 2m, `es - ea` = vapor pressure deficit

### Machine Learning Pipeline

Raw Sensor Data → Feature Engineering → Random Forest Classifier
                                              ↓
                              Predict: Water NOW / Wait / Skip
                                              ↓
                              Confidence Threshold Check
                                              ↓
                              Trigger Pump / Send Notification

**Features used:**
- Soil moisture (%), temperature (°C), humidity (%), light intensity (lux)
- Hour of day, day of week, crop growth stage
- Weather forecast (next 6h rain probability)
- Calculated ET₀ value
### Seasonal Water Forecast
Uses **ARIMA / LSTM** time-series forecasting to predict total water usage per week/month for resource planning.
## Dashboard
The web dashboard provides:
-  Real-time sensor readings (live charts)
-  Irrigation event log and history
-  Temperature & humidity trends
-  Active alerts and thresholds
-  Weekly water usage summary

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

## Acknowledgements
- [ThingSpeak IoT Platform](https://thingspeak.com) by MathWorks
- [OpenWeatherMap API](https://openweathermap.org)
- FAO Penman-Monteith ET₀ Reference (FAO Irrigation and Drainage Paper 56)
- Arduino & ESP32 open-source community
AUthor-Afreed,ashraf

> Built with ❤️ for sustainable agriculture | SR University, Warangal

