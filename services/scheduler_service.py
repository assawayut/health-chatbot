"""Scheduler service for periodic tasks like broadcasting PM2.5 reports"""

import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Optional

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for scheduling periodic tasks"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._started = False

    def start(self):
        """Start the scheduler"""
        if not self._started:
            self.scheduler.start()
            self._started = True
            logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler"""
        if self._started:
            self.scheduler.shutdown()
            self._started = False
            logger.info("Scheduler stopped")

    def add_pm25_broadcast_job(self, hour: int = 7, minute: int = 0):
        """
        Add job to broadcast PM2.5 report daily at specified time

        Args:
            hour: Hour to send (0-23), default 7 AM
            minute: Minute to send (0-59), default 0
        """
        from services.broadcast_service import get_broadcast_service

        async def broadcast_job():
            logger.info("Running scheduled PM2.5 broadcast...")
            try:
                service = get_broadcast_service()
                success = await service.broadcast_pm25_report()
                if success:
                    logger.info("Scheduled PM2.5 broadcast completed successfully")
                else:
                    logger.error("Scheduled PM2.5 broadcast failed")
            except Exception as e:
                logger.error(f"Error in scheduled broadcast: {e}")

        # Schedule for specified time, Bangkok timezone (Asia/Bangkok)
        self.scheduler.add_job(
            broadcast_job,
            CronTrigger(hour=hour, minute=minute, timezone="Asia/Bangkok"),
            id="pm25_broadcast",
            replace_existing=True
        )
        logger.info(f"PM2.5 broadcast scheduled for {hour:02d}:{minute:02d} daily (Bangkok time)")

    def add_multiple_broadcast_times(self, times: list):
        """
        Add multiple broadcast times

        Args:
            times: List of (hour, minute) tuples, e.g. [(7, 0), (12, 0), (18, 0)]
        """
        from services.broadcast_service import get_broadcast_service

        async def broadcast_job():
            logger.info("Running scheduled PM2.5 broadcast...")
            try:
                service = get_broadcast_service()
                success = await service.broadcast_pm25_report()
                if success:
                    logger.info("Scheduled PM2.5 broadcast completed successfully")
                else:
                    logger.error("Scheduled PM2.5 broadcast failed")
            except Exception as e:
                logger.error(f"Error in scheduled broadcast: {e}")

        for i, (hour, minute) in enumerate(times):
            self.scheduler.add_job(
                broadcast_job,
                CronTrigger(hour=hour, minute=minute, timezone="Asia/Bangkok"),
                id=f"pm25_broadcast_{i}",
                replace_existing=True
            )
            logger.info(f"PM2.5 broadcast scheduled for {hour:02d}:{minute:02d} (Bangkok time)")


# Singleton instance
_scheduler_service: Optional[SchedulerService] = None


def get_scheduler_service() -> SchedulerService:
    """Get singleton scheduler service"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service
