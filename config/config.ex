# Smart Watering System Configuration
# Copy to config.yaml and update with real values

thingspeak:
  channel_id: "YOUR_CHANNEL_ID"
  read_api_key: "YOUR_READ_KEY"
  write_api_key: "YOUR_WRITE_KEY"

weather:
  api_key: "YOUR_OPENWEATHERMAP_KEY"
  location: "Warangal,IN"
  units: "metric"

irrigation:
  soil_moisture_threshold: 30      # water when below this %
  pump_duration_seconds: 15        # base pump run time
  max_pump_duration_seconds: 120   # upper limit
  check_interval_minutes: 30       # scheduler interval

crop:
  type: "tomato"                   # tomato, wheat, maize, rice, cotton, soybean
  growth_stage: "flowering"        # initial, vegetative, flowering, ripening

site:
  latitude: 17.98
  longitude: 79.59
  elevation_m: 260

notifications:
  email: "your@email.com"
  email_password: "your_app_password"
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
