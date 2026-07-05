from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import atexit

_scheduler = None


def init_scheduler(app, fetch_fn, interval_minutes=30):
    """Initialize APScheduler to run fetch_fn immediately, then every interval_minutes."""
    global _scheduler

    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(daemon=True)

    _scheduler.add_job(
        func=lambda: fetch_fn(app),
        trigger=IntervalTrigger(minutes=interval_minutes),
        id='rss_fetch_job',
        name='Fetch RSS Feeds',
        replace_existing=True,
        next_run_time=datetime.now(),   # fire immediately on startup, then every interval
    )

    _scheduler.start()
    print(f"[Scheduler] RSS fetch job started — running now, then every {interval_minutes} min.")

    atexit.register(lambda: _scheduler.shutdown(wait=False))