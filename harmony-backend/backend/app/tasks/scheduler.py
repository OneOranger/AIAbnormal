"""APScheduler — 周级重训 + 6h 漂移检查(对齐文档 §3.4 Step 7)。"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from app.ml.scheduler.retrain_jobs import weekly_retrain_job, drift_check_job

_scheduler: AsyncIOScheduler | None = None


def start_scheduler():
    global _scheduler
    if _scheduler:
        return
    _scheduler = AsyncIOScheduler()

    # 文档要求:周级重训(每周一凌晨 3 点)
    _scheduler.add_job(
        weekly_retrain_job, CronTrigger(day_of_week="mon", hour=3, minute=0),
        id="weekly_retrain", replace_existing=True,
    )
    # 6h 漂移检查
    _scheduler.add_job(drift_check_job, "interval", hours=6, id="drift_check", replace_existing=True)

    _scheduler.start()
    logger.info("⏰ Scheduler started: weekly_retrain (mon 03:00) + drift_check (6h)")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("⏰ Scheduler stopped")
