"""Dust/Air Quality Service - fetches PM2.5 data from Air4Thai API"""

import httpx
import logging
import math
from typing import Optional, Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in kilometers using Haversine formula"""
    R = 6371  # Earth's radius in kilometers

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

# Air4Thai API endpoint
AIR4THAI_API_URL = "http://air4thai.pcd.go.th/forappV2/getAQI_JSON.php"

# AQI level descriptions in Thai
AQI_LEVELS = [
    {"max": 25, "level": "ดีมาก", "color": "🟦", "advice": "คุณภาพอากาศดีมาก เหมาะสำหรับกิจกรรมกลางแจ้งและการท่องเที่ยว"},
    {"max": 50, "level": "ดี", "color": "🟩", "advice": "คุณภาพอากาศดี สามารถทำกิจกรรมกลางแจ้งได้ตามปกติ"},
    {"max": 100, "level": "ปานกลาง", "color": "🟨", "advice": "ประชาชนทั่วไปสามารถทำกิจกรรมกลางแจ้งได้ตามปกติ ผู้ที่ต้องดูแลสุขภาพเป็นพิเศษควรลดกิจกรรมกลางแจ้ง"},
    {"max": 200, "level": "เริ่มมีผลกระทบต่อสุขภาพ", "color": "🟧", "advice": "ควรลดกิจกรรมกลางแจ้ง ผู้ที่มีโรคประจำตัวควรสวมหน้ากาก N95"},
    {"max": 300, "level": "มีผลกระทบต่อสุขภาพ", "color": "🟥", "advice": "หลีกเลี่ยงกิจกรรมกลางแจ้ง สวมหน้ากาก N95 หากจำเป็นต้องออกนอกบ้าน"},
    {"max": 999, "level": "อันตราย", "color": "🟤", "advice": "งดกิจกรรมกลางแจ้งทุกชนิด ปิดประตูหน้าต่าง ใช้เครื่องฟอกอากาศ"},
]

# Bangkok area stations (most commonly requested)
BANGKOK_STATIONS = ["02t", "03t", "05t", "10t", "11t", "12t", "50t", "52t", "53t", "54t", "59t", "61t"]


class DustService:
    """Service for fetching air quality data"""

    def __init__(self):
        self.cached_data: Optional[Dict] = None
        self.cache_time: Optional[datetime] = None
        self.cache_duration = 600  # 10 minutes cache

    async def get_all_stations(self) -> Optional[List[Dict]]:
        """Fetch all station data from Air4Thai API"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(AIR4THAI_API_URL)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("stations", [])
        except Exception as e:
            logger.error(f"Error fetching Air4Thai data: {e}")
        return None

    async def get_bangkok_average(self) -> Optional[Dict]:
        """Get average PM2.5 for Bangkok area"""
        stations = await self.get_all_stations()
        if not stations:
            return None

        pm25_values = []
        station_names = []

        for station in stations:
            if station.get("stationID") in BANGKOK_STATIONS:
                aqi_data = station.get("AQILast", {})
                pm25 = aqi_data.get("PM25", {})
                if pm25 and pm25.get("value"):
                    try:
                        value = float(pm25["value"])
                        if value > 0:  # Valid reading
                            pm25_values.append(value)
                            station_names.append(station.get("nameTH", ""))
                    except (ValueError, TypeError):
                        pass

        if pm25_values:
            avg = sum(pm25_values) / len(pm25_values)
            return {
                "area": "กรุงเทพมหานคร",
                "pm25": round(avg, 1),
                "station_count": len(pm25_values),
                "min": round(min(pm25_values), 1),
                "max": round(max(pm25_values), 1),
            }
        return None

    async def get_station_by_name(self, query: str) -> Optional[Dict]:
        """Find station by name search"""
        stations = await self.get_all_stations()
        if not stations:
            return None

        query_lower = query.lower()

        for station in stations:
            name_th = station.get("nameTH", "").lower()
            name_en = station.get("nameEN", "").lower()
            area = station.get("areaTH", "").lower()

            if query_lower in name_th or query_lower in name_en or query_lower in area:
                aqi_data = station.get("AQILast", {})
                pm25 = aqi_data.get("PM25", {})
                aqi = aqi_data.get("AQI", {})

                return {
                    "station_name": station.get("nameTH"),
                    "area": station.get("areaTH"),
                    "pm25": pm25.get("value") if pm25 else None,
                    "aqi": aqi.get("aqi") if aqi else None,
                    "time": aqi_data.get("date") + " " + aqi_data.get("time") if aqi_data.get("date") else None,
                }
        return None

    async def get_nearest_station(self, lat: float, lng: float) -> Optional[Dict]:
        """Find nearest station by coordinates"""
        stations = await self.get_all_stations()
        if not stations:
            return None

        nearest_station = None
        min_distance = float('inf')

        for station in stations:
            try:
                station_lat = float(station.get("lat", 0))
                station_lng = float(station.get("long", 0))

                if station_lat == 0 or station_lng == 0:
                    continue

                distance = haversine_distance(lat, lng, station_lat, station_lng)

                # Check if station has valid PM2.5 data
                aqi_data = station.get("AQILast", {})
                pm25 = aqi_data.get("PM25", {})
                if not pm25 or not pm25.get("value"):
                    continue

                if distance < min_distance:
                    min_distance = distance
                    nearest_station = {
                        "station_name": station.get("nameTH"),
                        "area": station.get("areaTH"),
                        "pm25": pm25.get("value"),
                        "aqi": aqi_data.get("AQI", {}).get("aqi"),
                        "time": f"{aqi_data.get('date', '')} {aqi_data.get('time', '')}".strip(),
                        "distance": round(distance, 1),
                        "lat": station_lat,
                        "lng": station_lng,
                    }
            except (ValueError, TypeError):
                continue

        return nearest_station

    def get_aqi_level(self, pm25: float) -> Dict:
        """Get AQI level info based on PM2.5 value"""
        for level in AQI_LEVELS:
            if pm25 <= level["max"]:
                return level
        return AQI_LEVELS[-1]

    async def get_dust_report(self, location: Optional[str] = None) -> str:
        """Get formatted dust report"""

        # If specific location requested, try to find it
        if location:
            station_data = await self.get_station_by_name(location)
            if station_data and station_data.get("pm25"):
                try:
                    pm25_val = float(station_data["pm25"])
                    level = self.get_aqi_level(pm25_val)

                    report = f"📍 สถานี: {station_data['station_name']}\n"
                    report += f"📍 พื้นที่: {station_data['area']}\n\n"
                    report += f"{level['color']} ค่า PM2.5: {pm25_val} μg/m³\n"
                    report += f"📊 ระดับ: {level['level']}\n\n"
                    report += f"💡 คำแนะนำ:\n{level['advice']}\n"

                    if station_data.get("time"):
                        report += f"\n🕐 อัพเดทล่าสุด: {station_data['time']}"

                    return report
                except (ValueError, TypeError):
                    pass

        # Default: Bangkok average
        bangkok_data = await self.get_bangkok_average()

        if bangkok_data:
            level = self.get_aqi_level(bangkok_data["pm25"])

            report = f"📍 พื้นที่: {bangkok_data['area']}\n"
            report += f"📊 จำนวนสถานีวัด: {bangkok_data['station_count']} สถานี\n\n"
            report += f"{level['color']} ค่า PM2.5 เฉลี่ย: {bangkok_data['pm25']} μg/m³\n"
            report += f"📈 ค่าต่ำสุด-สูงสุด: {bangkok_data['min']} - {bangkok_data['max']} μg/m³\n"
            report += f"📊 ระดับ: {level['level']}\n\n"
            report += f"💡 คำแนะนำ:\n{level['advice']}\n"
            report += f"\n🕐 ข้อมูลจาก: กรมควบคุมมลพิษ (Air4Thai)"

            return report

        return """ขออภัยค่ะ ไม่สามารถดึงข้อมูลค่าฝุ่นได้ในขณะนี้

กรุณาลองใหม่อีกครั้ง หรือตรวจสอบได้ที่:
🌐 http://air4thai.pcd.go.th/
📱 แอป Air4Thai"""

    async def get_dust_report_by_location(self, lat: float, lng: float) -> str:
        """Get formatted dust report for nearest station to given coordinates"""
        station_data = await self.get_nearest_station(lat, lng)

        if station_data and station_data.get("pm25"):
            try:
                pm25_val = float(station_data["pm25"])
                level = self.get_aqi_level(pm25_val)

                report = f"📍 สถานีใกล้คุณที่สุด: {station_data['station_name']}\n"
                report += f"📍 พื้นที่: {station_data['area']}\n"
                report += f"📏 ระยะห่าง: {station_data['distance']} กม.\n\n"
                report += f"{level['color']} ค่า PM2.5: {pm25_val} μg/m³\n"
                report += f"📊 ระดับ: {level['level']}\n\n"
                report += f"💡 คำแนะนำ:\n{level['advice']}\n"

                if station_data.get("time"):
                    report += f"\n🕐 อัพเดทล่าสุด: {station_data['time']}"

                report += "\n\n🌐 ข้อมูลจาก: กรมควบคุมมลพิษ (Air4Thai)"

                return report
            except (ValueError, TypeError):
                pass

        return """ขออภัยค่ะ ไม่พบสถานีวัดค่าฝุ่นใกล้ตำแหน่งของคุณ

กรุณาลองใหม่อีกครั้ง หรือตรวจสอบได้ที่:
🌐 http://air4thai.pcd.go.th/
📱 แอป Air4Thai"""


# Singleton instance
_dust_service: Optional[DustService] = None


def get_dust_service() -> DustService:
    """Get singleton dust service"""
    global _dust_service
    if _dust_service is None:
        _dust_service = DustService()
    return _dust_service
