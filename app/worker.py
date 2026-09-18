from __future__ import annotations

import time

from .db import SessionLocal, init_db
from .jobs import process_pending_jobs


def main() -> None:
    init_db()
    while True:
        with SessionLocal() as session:
            process_pending_jobs(session)
        time.sleep(10)


if __name__ == "__main__":
    main()
