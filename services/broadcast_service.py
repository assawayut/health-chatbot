"""Broadcast service for sending messages to all Line followers"""

import httpx
import logging
import asyncio
from typing import Optional, List

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
        """Get PM2.5 image URL from Google Sites using Playwright (headless browser)"""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                await page.goto(PM25_IMAGE_PAGE, wait_until="networkidle")

                # Wait for images to load
                await page.wait_for_selector("img.CENy8b", timeout=10000)

                # Try to find image in specific section first (PM2.5 report section)
                section = await page.query_selector("section#h\\.7f0feb644f138bc2_0")
                if section:
                    img = await section.query_selector("img.CENy8b")
                    if img:
                        src = await img.get_attribute("src")
                        if src and "lh3.googleusercontent.com" in src:
                            logger.info(f"Found PM2.5 image in target section: {src[:80]}...")
                            await browser.close()
                            return src

                # Fallback: find first portrait image
                images = await page.query_selector_all("img.CENy8b")
                for img in images:
                    src = await img.get_attribute("src")
                    if not src or "lh3.googleusercontent.com/sitesv" not in src:
                        continue

                    box = await img.bounding_box()
                    if box:
                        height = box.get("height", 0)
                        width = box.get("width", 0)
                        logger.info(f"Found image: {width:.0f}x{height:.0f} - {src[:60]}...")

                        # First portrait image with reasonable size
                        if height > width and height > 300:
                            logger.info(f"Selected first portrait image: {src[:80]}...")
                            await browser.close()
                            return src

                await browser.close()
                logger.warning("No suitable PM2.5 image found on page")
                return None

        except Exception as e:
            logger.error(f"Error getting PM2.5 image: {e}")
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
        """Fetch PM2.5 image and broadcast to all followers (image only)"""
        image_url = await self.get_pm25_image_url()

        if not image_url:
            logger.error("Could not get PM2.5 image URL")
            return False

        # Send image only
        return await self.broadcast_image(image_url)


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
