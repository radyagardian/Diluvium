import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base Directory Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
BMKG_CACHE_DIR = PROCESSED_DATA_DIR / "bmkg_cache"

# Ensure the local cache directory exists
BMKG_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# BMKG API Configuration
BMKG_API_BASE_URL = "https://api.bmkg.go.id/publik/prakiraan-cuaca"
BMKG_REQUEST_TIMEOUT = 10.0
BMKG_MAX_RETRIES = 3
BMKG_BASE_BACKOFF = 2.0
# Safe concurrency limit to respect BMKG's public rate limit (60 requests/minute)
BMKG_MAX_CONCURRENT_REQUESTS = 5

# Sub-district (adm4) Watchlist for Flood-Prone Areas across DKI Jakarta's 5 Administrative Cities and all DKI Jakarta regional codes start with province prefix '31.'
JAKARTA_FLOOD_PRONE_ADM4 = {
    # Central Jakarta 
    "31.71.03.1001": "Kemayoran, Central Jakarta",
    "31.71.07.1003": "Karet Tengsin, Tanah Abang, Central Jakarta",
    
    # North Jakarta 
    "31.72.01.1001": "Penjaringan (Pluit/Muara Angke), North Jakarta",
    "31.72.06.1001": "Kelapa Gading Timur, North Jakarta",
    
    # West Jakarta
    "31.73.02.1002": "Duri Kepa, Kebon Jeruk, West Jakarta",
    "31.73.03.1004": "Rawa Buaya, Cengkareng, West Jakarta",
    "31.73.08.1001": "Kembangan Selatan, West Jakarta",
    
    # South Jakarta 
    "31.74.01.1004": "Bukit Duri, Tebet, South Jakarta",
    "31.74.04.1005": "Pejaten Timur, Pasar Minggu, South Jakarta",
    "31.74.06.1002": "Pondok Pinang, Kebayoran Lama, South Jakarta",
    "31.74.07.1002": "Petogogan, Kebayoran Baru, South Jakarta",
    
    # East Jakarta 
    "31.75.03.1002": "Kampung Melayu, Jatinegara, East Jakarta",
    "31.75.03.1003": "Bidara Cina, Jatinegara, East Jakarta",
    "31.75.04.1004": "Cawang, Kramat Jati, East Jakarta",
    "31.75.06.1006": "Cipinang Melayu, Makasar, East Jakarta",
}

# ==========================================
# BPBD DKI Jakarta (Pantau Banjir AWLR) Config
# ==========================================
BPBD_API_BASE_URL = "https://poskobanjir.dsda.jakarta.go.id/api/v1/pintu-air"
BPBD_CACHE_DIR = PROCESSED_DATA_DIR / "bpbd_cache"
BPBD_CACHE_DIR.mkdir(parents=True, exist_ok=True)

BPBD_REQUEST_TIMEOUT = 10.0
BPBD_MAX_RETRIES = 3
BPBD_BASE_BACKOFF = 2.0

# Official BPBD Floodgate Thresholds (in cm) for Early Warning
# (Normal / Siaga 4, Waspada / Siaga 3, Kritis / Siaga 2, Bencana / Siaga 1)
JAKARTA_WATER_GATES = {
    "Katulampa": {
        "river": "Sungai Ciliwung Hulu",
        "normal_max": 80,
        "siaga3_min": 81,
        "siaga2_min": 151,
        "siaga1_min": 201,
        "lead_time_hours": 9.0  # Travel time of flood wave from Bogor to Manggarai
    },
    "Depok": {
        "river": "Sungai Ciliwung Tengah",
        "normal_max": 200,
        "siaga3_min": 201,
        "siaga2_min": 271,
        "siaga1_min": 351,
        "lead_time_hours": 4.5
    },
    "Manggarai": {
        "river": "Sungai Ciliwung Hilir / Pintu Air Utama",
        "normal_max": 750,
        "siaga3_min": 751,
        "siaga2_min": 851,
        "siaga1_min": 951,
        "lead_time_hours": 0.5
    },
    "Karet": {
        "river": "Banjir Kanal Barat",
        "normal_max": 450,
        "siaga3_min": 451,
        "siaga2_min": 551,
        "siaga1_min": 601,
        "lead_time_hours": 0.5
    },
    "Pasar Ikan": {
        "river": "Muara / Laut Jawa (Tidal/Rob)",
        "normal_max": 170,
        "siaga3_min": 171,
        "siaga2_min": 201,
        "siaga1_min": 251,
        "lead_time_hours": 0.0
    },
    "Krukut Hulu": {
        "river": "Sungai Krukut",
        "normal_max": 150, "siaga3_min": 151, "siaga2_min": 251, "siaga1_min": 301, "lead_time_hours": 3.0
    },
    "Pesanggrahan": {
        "river": "Sungai Pesanggrahan",
        "normal_max": 150, "siaga3_min": 151, "siaga2_min": 251, "siaga1_min": 301, "lead_time_hours": 3.0
    },
    "Angke Hulu": {
        "river": "Sungai Angke",
        "normal_max": 150, "siaga3_min": 151, "siaga2_min": 251, "siaga1_min": 301, "lead_time_hours": 3.0
    },
    "Waduk Pluit": {
        "river": "Polder Pluit",
        "normal_max": 0, "siaga3_min": 1, "siaga2_min": 50, "siaga1_min": 100, "lead_time_hours": 0.0
    },
    "Cipinang Hulu": {
        "river": "Sungai Cipinang",
        "normal_max": 150, "siaga3_min": 151, "siaga2_min": 201, "siaga1_min": 251, "lead_time_hours": 2.5
    },
    "Sunter Hulu": {
        "river": "Sungai Sunter",
        "normal_max": 150, "siaga3_min": 151, "siaga2_min": 201, "siaga1_min": 251, "lead_time_hours": 2.5
    },
    "Pulo Gadung": {
        "river": "Sistem Polder Pulo Gadung",
        "normal_max": 550, "siaga3_min": 551, "siaga2_min": 651, "siaga1_min": 751, "lead_time_hours": 1.0
    }
}