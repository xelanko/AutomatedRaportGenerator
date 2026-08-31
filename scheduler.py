"""
Scheduling support using APScheduler. Allows the report pipeline
to run on a cron-style schedule (daily/weekly/monthly) unattended.
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import config
import logger_setup

log = logger_setup.get_logger(__name__)


def schedule_job(job_func, cron_expression: str = None, job_id: str = "report_job"):
    """
    cron_expression example: "0 7 * * MON" -> every Monday at 07:00
    Fields: minute hour day month day_of_week
    """
    cron_expression = cron_expression or config.DEFAULT_SCHEDULE_CRON
    minute, hour, day, month, day_of_week = cron_expression.split()

    scheduler = BlockingScheduler()
    trigger = CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week)
    scheduler.add_job(job_func, trigger=trigger, id=job_id, replace_existing=True)

    log.info(f"Scheduled job '{job_id}' with cron '{cron_expression}'")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped")