import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Path, HTTPException, Request
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.preprocess import process_daily_post, process_hourly_post
from app.services.json_load import load_device_json
from app.services.recommendation import generate_and_update_recommendation

"""
Swagger UI
http://localhost:8000/v1/ssafyA104/AI/docs
http://i12a104.p.ssafy.io:8080/swagger-ui/index.html

http://i12a104.p.ssafy.io:8000/v1/ssafyA104/AI
http://localhost:8000/v1/ssafyA104/AI
"""

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter()

def create_response(status: int, message: str):
    return {
        "status": status,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/")
async def read_root():
    print("hello")
    return {"message": "hello"}

@router.post("/device/{deviceId}/report/daily")
async def post_daily_report(
    request: Request,
    deviceId: int = Path(..., title="Device ID", description="기기 ID"),
    data: dict = {},
    db: Session = Depends(get_db)
):
    logger.info("Received DAILY POST request for device_id: %s", deviceId)
    try:
        process_daily_post(db, data, deviceId)

        generate_and_update_recommendation(db, deviceId, request)

        return create_response(201, "리소스가 성공적으로 생성되었습니다.")
    except Exception as e:
        logger.error("Error processing DAILY POST for device_id %s: %s", deviceId, str(e))
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다.")
    
@router.post("/device/{deviceId}/report/hourly")
async def post_hourly_report(
    request: Request,
    deviceId: int = Path(..., title="Device ID", description="기기 ID"),
    data: dict = {},
    db: Session = Depends(get_db)
):
    logger.info("Received HOURLY POST request for device_id: %s", deviceId)
    try:
        process_hourly_post(db, data, deviceId)

        generate_and_update_recommendation(db, deviceId, request)

        return create_response(201, "리소스가 성공적으로 생성되었습니다.")
    except Exception as e:
        logger.error("Error processing HOURLY POST for device_id %s: %s", deviceId, str(e))
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다.")
    
@router.get("/device/{deviceId}/report/weekly")
async def get_weekly_report(
    deviceId: int = Path(..., title="Device ID", description="기기 ID"),
    db: Session = Depends(get_db)
):
    logger.info("Received GET request for WEEKLY report for device_id: %s", deviceId)
    
    result = load_device_json(db, deviceId)
    
    if not result:
        return {
            "status": "DEVICE_NOT_FOUND",
            "message": "기기를 찾을 수 없습니다.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    return result