from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from app.models.entities import SessionLocal

logger = logging.getLogger(__name__)


class ThreadJobRunner:
    """Runner MVP sostituibile in futuro con coda Celery/RQ."""

    def submit(self, fn: Callable, *args, **kwargs) -> None:
        def _target() -> None:
            db = SessionLocal()
            try:
                fn(db, *args, **kwargs)
            except Exception:
                logger.exception("job_failed")
            finally:
                db.close()

        thread = threading.Thread(target=_target, daemon=True)
        thread.start()


job_runner = ThreadJobRunner()
