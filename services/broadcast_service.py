"""Broadcast service for sending messages to all Line followers"""

import httpx
import logging
import re
from typing import Optional, List
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Google Sites page with PM2.5 image
PM25_IMAGE_PAGE = "https://sites.google.com/view/pm25plk/home"


class BroadcastService:
    """Service for broadcasting messages to Line followers"""

    def __init__(self, channel_access_token: str):
        self.channel_access_token = channel_access_token
        self.broadcast_url = "https://api.line.me/v2/bot/message/broadcast"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {channel_access_token}"
        }

    async def get_pm25_image_url(self) -> Optional[str]:
        """Scrape PM2.5 image URL from Google Sites"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(PM25_IMAGE_PAGE)
                if response.status_code != 200:
                    logger.error(f"Failed to fetch Google Sites page: {response.status_code}")
                    return None

                soup = BeautifulSoup(response.text, 'html.parser')

                # Find image with class containing CENy8b (Google Sites image class)
                img = soup.find('img', class_=re.compile(r'CENy8b'))
                if img and img.get('src'):
                    image_url = img['src']
                    logger.info(f"Found PM2.5 image: {image_url[:50]}...")
                    return image_url

                # Alternative: find any lh3.googleusercontent.com image
                for img in soup.find_all('img'):
                    src = img.get('src', '')
                    if 'lh3.googleusercontent.com' in src:
                        logger.info(f"Found PM2.5 image (alt): {src[:50]}...")
                        return src

                logger.warning("No PM2.5 image found on page")
                return None

        except Exception as e:
            logger.error(f"Error scraping PM2.5 image: {e}")
            return None

    async def broadcast_image(self, image_url: str, alt_text: str = "รายงานค่าฝุ่น PM2.5") -> bool:
        """Broadcast image to all followers"""
        try:
            payload = {
                "messages": [
                    {
                        "type": "image",
                        "originalContentUrl": image_url,
                        "previewImageUrl": image_url
                    }
                ]
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.broadcast_url,
                    headers=self.headers,
                    json=payload
                )

                if response.status_code == 200:
                    logger.info("Broadcast image sent successfully")
                    return True
                else:
                    logger.error(f"Broadcast failed: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error broadcasting image: {e}")
            return False

    async def broadcast_text(self, message: str) -> bool:
        """Broadcast text message to all followers"""
        try:
            payload = {
                "messages": [
                    {
                        "type": "text",
                        "text": message
                    }
                ]
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.broadcast_url,
                    headers=self.headers,
                    json=payload
                )

                if response.status_code == 200:
                    logger.info("Broadcast text sent successfully")
                    return True
                else:
                    logger.error(f"Broadcast failed: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Error broadcasting text: {e}")
            return False

    async def broadcast_pm25_report(self) -> bool:
        """Fetch PM2.5 image and broadcast to all followers"""
        image_url = await self.get_pm25_image_url()

        if not image_url:
            logger.error("Could not get PM2.5 image URL")
            return False

        # Send image
        success = await self.broadcast_image(image_url)

        if success:
            # Optionally send text with the image
            await self.broadcast_text(
                "📊 รายงานสถานการณ์ฝุ่น PM2.5 ประจำวัน\n\n"
                "ติดตามข้อมูลเพิ่มเติมได้ที่:\n"
                "🌐 https://air4thai.pcd.go.th\n\n"
                "พิมพ์ 'ตรวจสอบค่าฝุ่น' เพื่อดูค่าฝุ่นบริเวณใกล้คุณค่ะ"
            )

        return success


# Singleton instance
_broadcast_service: Optional[BroadcastService] = None


def get_broadcast_service(channel_access_token: str = None) -> BroadcastService:
    """Get singleton broadcast service"""
    global _broadcast_service
    if _broadcast_service is None:
        if channel_access_token is None:
            from config import get_settings
            channel_access_token = get_settings().line_channel_access_token
        _broadcast_service = BroadcastService(channel_access_token)
    return _broadcast_service
