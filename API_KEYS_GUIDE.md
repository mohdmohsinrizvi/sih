# 🔑 API Keys & Credentials — Full List

> Ye file me sab API keys hain jo chahiye, kahan se milengi, aur kaise use karein.

---

## 📋 Quick Summary

| # | Service | Key Chahiye? | Free? | Difficulty |
|---|---------|-------------|-------|------------|
| 1 | IMD (India Meteorological Dept) | ✅ Haan | ✅ Free | Easy |
| 2 | OpenWeatherMap | ✅ Haan | ✅ Free (1000/day) | Easy |
| 3 | NOAA Data | ❌ Nahi | ✅ Free | Easy |
| 4 | Wikipedia | ❌ Nahi | ✅ Free | Easy |
| 5 | PostgreSQL | ✅ Local creds | ✅ Free | N/A (already setup) |
| 6 | Redis | ❌ Default | ✅ Free | N/A (already setup) |
| 7 | MinIO | ✅ Local creds | ✅ Free | N/A (already setup) |
| 8 | Redpanda | ❌ No auth | ✅ Free | N/A (already setup) |

---

## 1. IMD API Key (India Meteorological Department)

**Kya hai:** India ka official weather data. Sabse reliable source for Indian weather.

### Steps:

1. **Jao:** https://mausam.imd.gov.in/
2. **Register karo:**
   - "Register" pe click karo
   - Naam, email, phone do
   - "Research" ya "Academic" purpose select karo
   - Submit karo
3. **Email verify karo:** IMD tumhe email bhejega verification link ke sath
4. **Login karo:** Apni credentials se login karo
5. **API Key lo:**
   - Dashboard pe "API Keys" ya "My API" section dekho
   - "Generate New Key" pe click karo
   - Key copy karo (e.g., `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
6. **Project me daalo:**
   ```
   .env file me add karo:
   IMD_API_KEY=your_api_key_here
   ```

### Rate Limits:
- 60 requests/minute (free tier)
- Research purpose ke liye zyada mil sakta hai

### API Endpoints:
```
Base URL: https://api.imd.gov.in

Current Weather: GET /current/weather?lat=28.6&lon=77.2&apikey=YOUR_KEY
Forecast: GET /forecast?city=Delhi&apikey=YOUR_KEY
Warnings: GET /warnings?state=Delhi&apikey=YOUR_KEY
```

---

## 2. OpenWeatherMap API Key

**Kya hai:** Duniya ka sabse popular weather API. 200+ countries ka data.

### Steps:

1. **Jao:** https://openweathermap.org/
2. **Sign Up karo:**
   - "Sign In" pe click karo
   - "Create an Account" pe click karo
   - Email, password, naam do
   - Email verify karo
3. **API Key lo:**
   - Login karo
   - "My API Keys" section me jao (https://home.openweathermap.org/api_keys)
   - Default ek key already hoti hai
   - Ya "Generate" pe click karo naya key ke liye
   - Key copy karo (e.g., `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)
4. **Project me daalo:**
   ```
   .env file me add karo:
   OPENWEATHER_API_KEY=your_api_key_here
   ```

### Important Note:
- API key **activate hone me 2-3 ghante lagte hain** (free tier)
- Turant kaam nahi karega, wait karo

### Rate Limits:
- Free tier: 1000 API calls/day
- 60 calls/minute
- 1 API call/second

### API Endpoints:
```
Base URL: https://api.openweathermap.org/data/2.5

Current Weather: GET /weather?q=Delhi&appid=YOUR_KEY&units=metric
5-Day Forecast: GET /forecast?q=Delhi&appid=YOUR_KEY&units=metric
Air Pollution: GET /air_pollution?lat=28.6&lon=77.2&appid=YOUR_KEY
```

### Free Tier me Kya Milta Hai:
```
✅ Current weather data
✅ 5-day / 3-hour forecast
✅ Historical weather data (last 5 days)
✅ Air pollution data
✅ Geocoding API
❌ Minute-by-minute forecast (paid)
❌ Hourly forecast beyond 48 hours (paid)
```

---

## 3. NOAA Data (No Key Required)

**Kya hai:** America ka National Oceanic and Atmospheric Administration. Historical weather data free me milta hai.

### Steps:

1. **Jao:** https://www.ncdc.noaa.gov/data-access
2. **CSV Download karo:**
   - "Global Historical Climatology Network" pe click karo
   - India select karo
   - Date range select karo
   - Download pe click karo
3. **Project me daalo:**
   ```
   data/noaa/ folder me CSV files daalo
   Config me URL update karo
   ```

### Koi Key Nahi Chahiye!
- Sab kuch public hai
- Bulk download available hai
- Daily, monthly, yearly data milta hai

---

## 4. Wikipedia Weather Feeds (No Key Required)

**Kya hai:** Wikipedia se weather-related articles ka data.

### Steps:

1. **Automatic hai** — kuch karna nahi padta
2. **Wikipedia API use karta hai** jo free hai
3. **Rate limit:** 200 requests/second (more than enough)

### Configuration:
```
config/sources.yaml me:
- source_id: "india_wiki_feeds"
  enabled: true  # False se True karo
  url: "https://en.wikipedia.org/wiki/Weather_in_India"
```

---

## 5. PostgreSQL Credentials (Already Setup)

**Kya hai:** Database credentials jo already set hai.

### Current Values:
```
Host: localhost
Port: 5432
Database: weatherdb
Username: weather
Password: weather
```

### .env File:
```
DATABASE_URL=postgresql+asyncpg://weather:weather@localhost:5432/weatherdb
DATABASE_URL_SYNC=postgresql://weather:weather@localhost:5432/weatherdb
```

### Password Change Karna Ho To:
```sql
-- PostgreSQL me jao
docker exec -it weather-postgres psql -U weather -d weatherdb

-- Password change karo
ALTER USER weather WITH PASSWORD 'new_secure_password';
```

---

## 6. Redis Credentials (Default)

**Kya hai:** In-memory cache. Default me koi password nahi hai.

### Current Values:
```
Host: localhost
Port: 6379
Password: (none)
```

### .env File:
```
REDIS_URL=redis://localhost:6379/0
```

### Password Set Karna Ho To:
```bash
# redis.conf me:
requirepass your_secure_password

# .env me update karo:
REDIS_URL=redis://:your_secure_password@localhost:6379/0
```

---

## 7. MinIO Credentials (Already Setup)

**Kya hai:** File storage (photos, videos, large files).

### Current Values:
```
Endpoint: localhost:9000
Access Key: minioadmin
Secret Key: minioadmin
```

### .env File:
```
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=weather-data
```

### Password Change Karna Ho To:
```bash
# MinIO console pe jao: http://localhost:9001
# Login: minioadmin / minioadmin
# Access Keys section me new key banao
```

---

## 8. Redpanda (No Auth Required)

**Kya hai:** Message queue. Default me koi authentication nahi hai.

### Current Values:
```
Bootstrap Servers: localhost:19092
```

### .env File:
```
REDPANDA_BOOTSTRAP_SERVERS=localhost:19092
```

---

## 📁 Complete .env File Template

Ye sab keys ek jagah rakhne ke liye `.env` file banao:

```env
# ============================================
# National Weather Platform - Environment
# ============================================

# --- DATABASE ---
DATABASE_URL=postgresql+asyncpg://weather:weather@localhost:5432/weatherdb
DATABASE_URL_SYNC=postgresql://weather:weather@localhost:5432/weatherdb

# --- REDIS ---
REDIS_URL=redis://localhost:6379/0

# --- REDPANDA (Kafka) ---
REDPANDA_BOOTSTRAP_SERVERS=localhost:19092

# --- MINIO (File Storage) ---
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=weather-data

# --- API KEYS (Real Data Sources) ---

# IMD (India Meteorological Department)
# Get from: https://mausam.imd.gov.in/
IMD_API_KEY=your_imd_api_key_here

# OpenWeatherMap
# Get from: https://home.openweathermap.org/api_keys
OPENWEATHER_API_KEY=your_openweather_api_key_here

# --- API SERVER ---
API_HOST=0.0.0.0
API_PORT=8000

# --- OTHER ---
DATA_DIR=./data
SCHEMA_VERSION=1.0
```

---

## ⚠️ Important Security Notes

1. **`.env` file kabhi commit mat karo** git me
   ```bash
   # .gitignore me daalo:
   echo ".env" >> .gitignore
   ```

2. **Production me passwords strong rakho**
   ```bash
   # Password generate karo:
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Keys rotate karo** — har 3-6 months me naya key banao

4. **Minimal permissions do** — sirf itna access do jitna zaruri hai

---

## 🎯 Hackathon Ke Liye Kya Chahiye?

| Priority | Service | Status |
|----------|---------|--------|
| 🔴 MUST | Synthetic Data | ✅ Already Working |
| 🔴 MUST | PostgreSQL | ✅ Already Working |
| 🔴 MUST | Redis | ✅ Already Working |
| 🔴 MUST | MinIO | ✅ Already Working |
| 🟡 NICE TO HAVE | IMD API | ⏳ Apply karo |
| 🟡 NICE TO HAVE | OpenWeatherMap | ⏳ Apply karo |
| 🟢 OPTIONAL | NOAA Data | ✅ Free, no key |
| 🟢 OPTIONAL | Wikipedia | ✅ Free, no key |

**Recommendation:**
1. Pehle **synthetic data** pe demo do — sab kuch kaam karta hai
2. **Hackathon se pehle 1 week** pe IMD aur OpenWeatherMap ke liye apply karo
3. Agar key mil jaye to **real data** ka demo bhi do — judge impress honge

---

**Last Updated:** 25 August 2026
