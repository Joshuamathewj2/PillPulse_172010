from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.medicines import is_active, normalize_times
from app.core import clock
from app.database.db import get_db
from app.models.adherence_log import AdherenceLog
from app.models.medicine import Medicine

router = APIRouter(prefix="/adherence", tags=["adherence"])


def daily_breakdown(db: Session, user_id: str, days: int = 7) -> list[dict]:
    """Expected vs taken doses per day, computed from the schedule and the adherence log."""
    meds = db.query(Medicine).filter(Medicine.user_id == user_id).all()
    logs = db.query(AdherenceLog).filter(AdherenceLog.user_id == user_id, AdherenceLog.taken_status.is_(True)).all()
    taken_by_day: dict = {}
    for log in logs:
        if log.timestamp:
            taken_by_day.setdefault(log.timestamp.date(), set()).add((log.medicine_id, log.scheduled_time))

    today = clock.today()
    now_hm = clock.now().strftime("%H:%M")
    out = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        expected = set()
        for med in meds:
            if not is_active(med, day):
                continue
            for t in normalize_times(med.schedule_times):
                if day < today or t <= now_hm:  # only count doses whose time has come
                    expected.add((med.medicine_id, t))
        taken = taken_by_day.get(day, set())
        taken_expected = len(expected & taken)
        extra = len(taken - expected)  # taken early, before the slot time
        n_taken = taken_expected + extra
        n_expected = len(expected) + extra
        out.append(
            {
                "date": day.isoformat(),
                "day": day.strftime("%a"),
                "expected": n_expected,
                "taken": n_taken,
                "missed": max(n_expected - n_taken, 0),
                "rate": round(100 * n_taken / n_expected, 1) if n_expected else None,
            }
        )
    return out


@router.get("/score")
def get_adherence_score(user_id: str, days: int = 7, db: Session = Depends(get_db)):
    breakdown = daily_breakdown(db, user_id, days)
    expected = sum(d["expected"] for d in breakdown)
    taken = sum(d["taken"] for d in breakdown)
    return {
        "score": round(100 * taken / expected, 1) if expected else None,
        "taken": taken,
        "expected": expected,
        "days": days,
        "has_data": expected > 0,
    }


@router.get("/weekly")
def get_weekly(user_id: str, db: Session = Depends(get_db)):
    return daily_breakdown(db, user_id, 7)


@router.get("/missed")
def get_missed_doses(user_id: str, db: Session = Depends(get_db)):
    today = clock.today()
    now_hm = clock.now().strftime("%H:%M")
    details = []
    for med in db.query(Medicine).filter(Medicine.user_id == user_id).all():
        if not is_active(med, today):
            continue
        taken = {
            l.scheduled_time
            for l in db.query(AdherenceLog).filter(
                AdherenceLog.medicine_id == med.medicine_id,
                AdherenceLog.user_id == user_id,
                AdherenceLog.taken_status.is_(True),
            )
            if l.timestamp and l.timestamp.date() == today
        }
        for t in normalize_times(med.schedule_times):
            if t < now_hm and t not in taken:
                details.append({"medicine_name": med.medicine_name, "scheduled_time": t})
    return {"missed_doses": len(details), "details": details}
