"""
Health Assessment Chatbot for PM2.5/Air Pollution
Line Messaging API webhook server
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    AsyncApiClient,
    AsyncMessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, LocationMessageContent
from linebot.v3.exceptions import InvalidSignatureError

from config import get_settings
from handlers.message_handler import get_message_handler
from services.scheduler_service import get_scheduler_service
from services.broadcast_service import get_broadcast_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Lazy initialization for Line SDK
_line_handler: WebhookHandler = None
_line_api: AsyncMessagingApi = None
_api_client: AsyncApiClient = None


def _ensure_line_initialized():
    """Initialize Line SDK lazily"""
    global _line_handler, _line_api, _api_client

    if _line_handler is None:
        settings = get_settings()
        _line_handler = WebhookHandler(settings.line_channel_secret)

        configuration = Configuration(
            access_token=settings.line_channel_access_token
        )
        _api_client = AsyncApiClient(configuration)
        _line_api = AsyncMessagingApi(_api_client)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Health Assessment Chatbot...")
    _ensure_line_initialized()

    # Start scheduler for periodic broadcasts
    scheduler = get_scheduler_service()
    scheduler.start()
    # Schedule PM2.5 broadcast (Bangkok time)
    scheduler.add_multiple_broadcast_times([(11, 0)])

    yield

    logger.info("Shutting down...")
    scheduler.stop()
    if _api_client:
        await _api_client.close()


app = FastAPI(
    title="Health Assessment Chatbot",
    description="Line chatbot for PM2.5 health assessment",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Health Assessment Chatbot is running"}


@app.post("/broadcast")
async def manual_broadcast():
    """Manually trigger PM2.5 broadcast (for testing)"""
    logger.info("Manual broadcast triggered")
    service = get_broadcast_service()
    success = await service.broadcast_pm25_report()
    return {"status": "ok" if success else "failed", "message": "Broadcast sent" if success else "Broadcast failed"}


@app.post("/webhook")
async def webhook(request: Request):
    """Line webhook endpoint"""
    _ensure_line_initialized()

    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    body_text = body.decode("utf-8")

    logger.info(f"Received webhook request")

    try:
        events = _line_handler.parser.parse(body_text, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        if isinstance(event, MessageEvent):
            if isinstance(event.message, TextMessageContent):
                await handle_text_message(event)
            elif isinstance(event.message, LocationMessageContent):
                await handle_location_message(event)

    return {"status": "ok"}


async def handle_text_message(event: MessageEvent):
    """Handle incoming text messages"""
    user_id = event.source.user_id
    text = event.message.text
    reply_token = event.reply_token

    logger.info(f"User [{user_id[:8]}...]: {text}")

    # Get response from message handler
    handler = get_message_handler()
    response = await handler.handle_message(user_id, text)

    logger.info(f"Bot response: {response[:50]}...")

    # Send reply
    try:
        await _line_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=response)]
            )
        )
    except Exception as e:
        logger.error(f"Error sending reply: {e}")


async def handle_location_message(event: MessageEvent):
    """Handle incoming location messages"""
    user_id = event.source.user_id
    latitude = event.message.latitude
    longitude = event.message.longitude
    reply_token = event.reply_token

    logger.info(f"User [{user_id[:8]}...]: Location ({latitude}, {longitude})")

    # Get response from message handler
    handler = get_message_handler()
    response = await handler.handle_location(user_id, latitude, longitude)

    logger.info(f"Bot response: {response[:50]}...")

    # Send reply
    try:
        await _line_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=response)]
            )
        )
    except Exception as e:
        logger.error(f"Error sending reply: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
