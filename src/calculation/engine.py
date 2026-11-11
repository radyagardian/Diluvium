import os
import re
import json
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
import geopandas as gpd

# Import kontrak data yang valid langsung dari src/schemas.py
from src.schemas import CalculationInput, HazardPrediction

# Konfigurasi direktori proyek secara dinamis
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
BMKG_CACHE_DIR = PROCESSED_DIR / "bmkg_cache"


# note!! = masih hardcoded, ngambil contoh (tebet) kalkulasi, nunggu orchestrator jadi

# =====================================================================
# 1. FUNGSI PEMROSESAN & STRUKTURISASI DATA STATIS (KAN-19)
# =====================================================================

def ekstrak_max_ketinggian(ketinggian_str: Any) -> int:
    """
    Mengekstrak angka maksimum dari format string ketinggian air pada CSV historis
    (contoh: "10 s/d 220" -> 220) agar bisa dihitung secara numerik.
    """
    try:
        angka = re.findall(r'\d+', str(ketinggian_str))
        if angka:
            return max(map(int, angka))
        return 0
    except Exception:
        return 0


def tentukan_tingkat_bahaya(kedalaman_cm: float) -> str:
    """
    Klasifikasi tingkat bahaya banjir berdasarkan Perka BNPB No. 2 Tahun 2012.
    """
    if kedalaman_cm > 150:
        return "Tinggi"
    elif 75 <= kedalaman_cm <= 150:
        return "Sedang"
    else:
        return "Rendah"


def structure_historical_flood_data() -> None:
    """
    KAN-19: Membersihkan dataset CSV riwayat banjir dari Jakarta Open Data
    serta menyaring kolom yang relevan untuk model hidrologi.
    """
    raw_csv_path = RAW_DIR / "jakarta_flood_history.csv"
    processed_csv_path = PROCESSED_DIR / "structured_flood_history.csv"
    
    if raw_csv_path.exists():
        print("[1] Memproses CSV Jakarta Open Data...")
        df = pd.read_csv(raw_csv_path)
        df.columns = df.columns.str.strip().str.lower()
        
        kolom_penting = [
            'kota_administrasi', 
            'kecamatan', 
            'kelurahan', 
            'ketinggian_air', 
            'tgl_kejadian'
        ]
        
        # Ambil hanya kolom yang tersedia di CSV agar tidak KeyError
        kolom_tersedia = [col for col in kolom_penting if col in df.columns]
        df = df[kolom_tersedia].copy()
        
        if 'ketinggian_air' in df.columns:
            df['ketinggian_maks_cm'] = df['ketinggian_air'].apply(ekstrak_max_ketinggian)
            df['tingkat_bahaya'] = df['ketinggian_maks_cm'].apply(tentukan_tingkat_bahaya)
            
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(processed_csv_path, index=False)
        print(f"--> Selesai: {processed_csv_path}")
    else:
        print(f"[!] File tidak ditemukan: {raw_csv_path}")


def process_spatial_hazard_layer() -> None:
    """
    KAN-19: Memproses data spasial batas wilayah / bahaya banjir dari data/raw/
    dan menstandarisasi CRS ke WGS84 (EPSG:4326).
    """
    raw_geo_path = RAW_DIR / "inarisk_flood_hazard.geojson"
    processed_geo_path = PROCESSED_DIR / "structured_inarisk_hazard.geojson"
    
    print("[2] Memproses data spasial bahaya banjir...")
    if raw_geo_path.exists():
        try:
            gdf = gpd.read_file(raw_geo_path)
            if gdf.empty:
                print("[!] Peringatan: File spasial kosong.")
                return

            if gdf.crs is None:
                gdf.set_crs(epsg=4326, inplace=True)
            elif gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs(epsg=4326)
                
            PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
            gdf.to_file(processed_geo_path, driver="GeoJSON")
            print(f"--> Selesai: {processed_geo_path}")
        except Exception as e:
            print(f"[!] Terjadi kesalahan saat memproses file spasial: {e}")
    else:
        print(f"[!] File spasial tidak ditemukan: {raw_geo_path}")


# =====================================================================
# 2. MESIN KALKULASI HIDROLOGI & SPASIAL (CALCULATION AGENT)
# =====================================================================

class HydrologicalCalculationEngine:
    """
    Mesin utama Calculation Agent untuk mengestimasi waktu kedatangan banjir (onset),
    kedalaman genangan (depth), radius sebaran, dan skor kepercayaan (confidence).
    """

    def __init__(self):
        self.history_df = pd.DataFrame()
        self.hazard_gdf = gpd.GeoDataFrame()
        self._load_reference_data()

    def _load_reference_data(self) -> None:
        """Memuat dataset hasil pemrosesan KAN-19 dari penyimpanan lokal."""
        csv_path = PROCESSED_DIR / "structured_flood_history.csv"
        geo_path = PROCESSED_DIR / "structured_inarisk_hazard.geojson"

        if csv_path.exists():
            try:
                self.history_df = pd.read_csv(csv_path)
            except Exception as e:
                print(f"[!] Gagal memuat CSV historis: {e}")

        if geo_path.exists():
            try:
                self.hazard_gdf = gpd.read_file(geo_path)
            except Exception as e:
                print(f"[!] Gagal memuat GeoJSON spasial: {e}")

    def _resolve_area_metadata(self, area_id: str) -> Dict[str, Optional[str]]:
        """
        Mencari nama kelurahan dan kecamatan dari kode adm4 (area_id)
        dengan memeriksa cache BMKG lokal jika tersedia.
        """
        clean_code = area_id.replace(".", "_")
        cache_candidates = [
            BMKG_CACHE_DIR / f"bmkg_{clean_code}.json",
            BASE_DIR / ".cache" / f"bmkg_{clean_code}.json"
        ]

        for cache_file in cache_candidates:
            if cache_file.exists():
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        lokasi = data.get("lokasi", {})
                        return {
                            "kelurahan": lokasi.get("desa", "").strip().upper(),
                            "kecamatan": lokasi.get("kecamatan", "").strip().upper()
                        }
                except Exception:
                    pass

        # Fallback jika area_id yang dikirim langsung berupa teks nama daerah
        return {
            "kelurahan": area_id.strip().upper(),
            "kecamatan": area_id.strip().upper()
        }

    def _get_historical_baseline(self, area_id: str) -> float:
        """
        Mengambil baseline kedalaman banjir historis (cm) untuk area target.
        """
        if self.history_df.empty or 'ketinggian_maks_cm' not in self.history_df.columns:
            return 20.0  # Baseline konservatif jika data historis belum termuat

        meta = self._resolve_area_metadata(area_id)
        kel_target = meta.get("kelurahan")
        kec_target = meta.get("kecamatan")

        # 1. Coba cocokkan berdasarkan tingkat Kelurahan
        if 'kelurahan' in self.history_df.columns and kel_target:
            kel_match = self.history_df[
                self.history_df['kelurahan'].astype(str).str.strip().str.upper() == kel_target
            ]
            if not kel_match.empty:
                return float(kel_match['ketinggian_maks_cm'].median())

        # 2. Jika tidak ketemu, agregasi berdasarkan tingkat Kecamatan
        if 'kecamatan' in self.history_df.columns and kec_target:
            kec_match = self.history_df[
                self.history_df['kecamatan'].astype(str).str.strip().str.upper() == kec_target
            ]
            if not kec_match.empty:
                return float(kec_match['ketinggian_maks_cm'].median())

        # 3. Default rata-rata seluruh Jakarta
        return float(self.history_df['ketinggian_maks_cm'].median())

    def calculate_hazard(self, calc_input: CalculationInput) -> HazardPrediction:
        """
        Menghitung prediksi bahaya banjir berdasarkan input telemetri (CalculationInput)
        dan menghasilkan output sesuai kontrak skema (HazardPrediction).
        """
        # 1. Ambil baseline historis wilayah (dibatasi maks 60 cm sebagai faktor kerentanan topografi)
        hist_baseline = self._get_historical_baseline(calc_input.area_id)
        topographic_base_cm = min(hist_baseline * 0.4, 60.0)

        # 2. Hitung kontribusi limpasan curah hujan lokal (mm/jam -> cm genangan)
        rainfall_contribution_cm = calc_input.rainfall_rate_mm * 1.2

        # 3. Hitung kontribusi luapan sungai dari 3 Pintu Air utama (ambang batas normal BPBD)
        # Katulampa (Normal < 80cm), Depok (Normal < 200cm), Manggarai (Normal < 750cm)
        katulampa_excess = max(0.0, calc_input.katulampa_level_cm - 80.0)
        depok_excess = max(0.0, calc_input.depok_level_cm - 200.0)
        manggarai_excess = max(0.0, calc_input.manggarai_level_cm - 750.0)

        river_surge_cm = (
            (katulampa_excess * 0.15) +
            (depok_excess * 0.25) +
            (manggarai_excess * 0.45)
        )

        # Total Prediksi Kedalaman Genangan (cm)
        if calc_input.rainfall_rate_mm == 0 and river_surge_cm == 0:
            predicted_depth_cm = 0.0
        else:
            predicted_depth_cm = round(topographic_base_cm + rainfall_contribution_cm + river_surge_cm, 2)

        # 4. Estimasi Waktu Kedatangan Air / Onset Time (jam)
        # Propagasi gelombang banjir dari Katulampa -> Depok -> Manggarai
        if manggarai_excess > 100 or calc_input.rainfall_rate_mm >= 100.0:
            # Limpasan lokal ekstrem atau Manggarai sudah Siaga 1/2
            estimated_arrival_hours = 0.5
        elif manggarai_excess > 0 or calc_input.rainfall_rate_mm >= 50.0:
            estimated_arrival_hours = 1.5
        elif depok_excess > 50:
            # Air kiriman sudah berada di Depok (~3-4 jam menuju hilir Jakarta)
            estimated_arrival_hours = 3.5
        elif katulampa_excess > 50:
            # Air kiriman baru melewati bendung Katulampa Bogor (~6-9 jam menuju Jakarta)
            estimated_arrival_hours = 6.5
        else:
            estimated_arrival_hours = 9.0

        # 5. Estimasi Radius Sebaran Genangan (km)
        if predicted_depth_cm <= 0:
            inundation_radius_km = 0.0
        else:
            # Skala proporsional terhadap kedalaman dan tekanan pintu air
            inundation_radius_km = round(min(5.0, max(0.2, (predicted_depth_cm / 100.0) * 1.2)), 2)

        # 6. Skor Kepercayaan Statistik / Confidence Score (0.0 - 1.0)
        confidence = 0.65  # Base confidence
        if not self.history_df.empty:
            confidence += 0.15
        if not self.hazard_gdf.empty:
            confidence += 0.10
        if calc_input.rainfall_rate_mm > 0 or river_surge_cm > 0:
            confidence += 0.05
        confidence_score = round(min(1.0, confidence), 2)

        # Kembalikan objek sesuai kontrak HazardPrediction di src/schemas.py
        return HazardPrediction(
            area_id=calc_input.area_id,
            estimated_arrival_hours=estimated_arrival_hours,
            predicted_depth_cm=predicted_depth_cm,
            inundation_radius_km=inundation_radius_km,
            confidence_score=confidence_score
        )


# Fungsi helper langsung jika dipanggil oleh MCP Server (src/mcp_server.py)
def run_hydrological_calculation(calc_input: CalculationInput) -> HazardPrediction:
    engine = HydrologicalCalculationEngine()
    return engine.calculate_hazard(calc_input)


if __name__ == "__main__":
    # 1. Pastikan data referensi KAN-19 terstruktur
    structure_historical_flood_data()
    process_spatial_hazard_layer()

    # 2. Uji coba kalkulasi menggunakan skema asli dari src/schemas.py
    print("\n[3] Menguji HydrologicalCalculationEngine dengan skema asli...")
    engine = HydrologicalCalculationEngine()

    sample_input = CalculationInput(
        katulampa_level_cm=160.0,
        depok_level_cm=270.0,
        manggarai_level_cm=860.0,
        rainfall_rate_mm=65.5,
        area_id="31.74.01.1004"  # Contoh kode adm4 Kelurahan Tebet Timur / sekitarnya
    )

    prediction = engine.calculate_hazard(sample_input)
    print("\n--- HASIL PREDIKSI BAHAYA (HazardPrediction) ---")
    print(prediction.model_dump_json(indent=2))