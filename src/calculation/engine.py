import os
import re
import pandas as pd
import geopandas as gpd

# Menyiapkan rute direktori
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

def ekstrak_max_ketinggian(ketinggian_str):
    """
    Mengekstrak angka maksimum dari format string ketinggian air.
    (misal: "10 s/d 220" -> 220) agar bisa dihitung secara numerik.
    """
    try:
        angka = re.findall(r'\d+', str(ketinggian_str))
        if angka:
            # Mengambil angka paling besar jika ada rentang
            return max(map(int, angka))
        return 0
    except:
        return 0

def tentukan_tingkat_bahaya(kedalaman_cm):
    """
    Klasifikasi tingkat bahaya banjir berdasarkan Perka BNPB No. 2 Tahun 2012.
    """
    if kedalaman_cm > 150:
        return "Tinggi"
    elif 75 <= kedalaman_cm <= 150:
        return "Sedang"
    else:
        return "Rendah"

def structure_historical_flood_data():
    """
    KAN-19: Membersihkan dataset CSV riwayat banjir dari Jakarta Open Data
    serta membuang kolom yang tidak relevan.
    """
    raw_csv_path = os.path.join(RAW_DIR, "jakarta_flood_history.csv")
    processed_csv_path = os.path.join(PROCESSED_DIR, "structured_flood_history.csv")
    
    if os.path.exists(raw_csv_path):
        print("[1] Memproses CSV Jakarta Open Data...")
        df = pd.read_csv(raw_csv_path)
        
        # Standardisasi nama kolom menjadi lowercase
        df.columns = df.columns.str.strip().str.lower()
        
        # Filter hanya kolom yang relevan secara hidrologis/geografis
        kolom_penting = [
            'kota_administrasi', 
            'kecamatan', 
            'kelurahan', 
            'ketinggian_air', 
            'tgl_kejadian'
        ]
        
        try:
            # Gunakan .copy() agar tidak terkena peringatan SettingWithCopyWarning pandas
            df = df[kolom_penting].copy()
            
            # Buat kolom baru berbasis perhitungan matematis
            df['ketinggian_maks_cm'] = df['ketinggian_air'].apply(ekstrak_max_ketinggian)
            df['tingkat_bahaya'] = df['ketinggian_maks_cm'].apply(tentukan_tingkat_bahaya)
            
        except KeyError as e:
            print(f"[!] Peringatan: Ada kolom yang tidak ditemukan di CSV asli: {e}")
        
        # Simpan ke folder processed
        df.to_csv(processed_csv_path, index=False)
        print(f"--> Selesai: {processed_csv_path}")
    else:
        print(f"[!] File tidak ditemukan: {raw_csv_path}")

def process_spatial_hazard_layer():
    """
    KAN-19: Memproses data spasial bahaya banjir dari file lokal data/raw/
    sebagai fallback karena pembatasan 403 Forbidden pada ArcGIS REST API BNPB.
    """
    raw_geo_path = os.path.join(RAW_DIR, "inarisk_flood_hazard.geojson")
    processed_geo_path = os.path.join(PROCESSED_DIR, "structured_inarisk_hazard.geojson")
    
    print("[2] Memproses data spasial batas kelurahan / bahaya banjir...")
    if os.path.exists(raw_geo_path):
        try:
            gdf = gpd.read_file(raw_geo_path)
            
            if gdf.empty:
                print("[!] Peringatan: File spasial kosong.")
                return

            print("--> Standarisasi koordinat (CRS) ke format WGS84 (EPSG:4326)...")
            if gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs(epsg=4326)
                
            gdf.to_file(processed_geo_path, driver="GeoJSON")
            print(f"--> Selesai: {processed_geo_path}")
            
        except Exception as e:
            print(f"[!] Terjadi kesalahan saat memproses file spasial: {e}")
    else:
        print(f"[!] File spasial tidak ditemukan di: {raw_geo_path}")
        print("[!] Tips: Letakkan file batas kelurahan / bahaya banjir .geojson di data/raw/.")

if __name__ == "__main__":
    # Pastikan folder ada
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    # Jalankan kedua fungsi
    structure_historical_flood_data()
    process_spatial_hazard_layer()