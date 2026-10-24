from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from app.services.prescription import extractors, process_prescription
from app.services.prescription.preprocess import InvalidImageError
from app.services.prescription.sig_parser import DayPlan, parse_sig

router = APIRouter(prefix="/api", tags=["prescription"])

MAX_BYTES = 10 * 1024 * 1024


@router.post("/predict")
async def predict(
    image: UploadFile = File(...),
    breakfast: Optional[str] = Form(None),
    lunch: Optional[str] = Form(None),
    dinner: Optional[str] = Form(None),
    bedtime: Optional[str] = Form(None),
):
    """Read a prescription photo and return a verified dose schedule.

    Optional form fields let the patient's own meal times drive the schedule.
    """
    data = await image.read()
    if not data:
        return JSONResponse(status_code=400, content={"success": False, "error": "No image uploaded"})
    if len(data) > MAX_BYTES:
        return JSONResponse(status_code=413, content={"success": False, "error": "Image is larger than 10 MB"})

    plan = DayPlan()
    for field, value in (("breakfast", breakfast), ("lunch", lunch), ("dinner", dinner), ("bedtime", bedtime)):
        if value:
            setattr(plan, field, value)
    try:
        return await run_in_threadpool(process_prescription, data, plan)
    except InvalidImageError as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})
    except extractors.EngineUnavailable as e:
        return JSONResponse(status_code=503, content={"success": False, "error": str(e)})


@router.get("/engines")
def engines():
    return {"available": extractors.available_engines(), "order": [e.name for e in extractors.engine_chain()]}


@router.get("/parse-sig")
def parse_sig_endpoint(text: str):
    """Debug/learning endpoint: see how a dosing instruction is interpreted."""
    sig = parse_sig(text)
    return {
        "frequency": sig.frequency_label,
        "times": sig.times,
        "dose": sig.dose_qty,
        "unit": sig.dose_unit,
        "food": sig.food_relation,
        "duration_days": sig.duration_days,
        "total_quantity": sig.total_quantity,
        "as_needed": sig.as_needed,
        "confidence": sig.confidence,
    }
