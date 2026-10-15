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