import json
import logging
from sqlalchemy.orm import Session
from app.database.crud import get_device, get_hourly_data, get_daily_data, get_recommendation

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def load_device_json(db: Session, device_id: int):
    logger.info("Loading JSON data for device_id: %s", device_id)
    device = get_device(db, device_id)
    if not device:
        logger.warning("Device %s not found", device_id)
        return {}
    
    hourly = get_hourly_data(db, device_id)
    daily = get_daily_data(db, device_id)
    reco = get_recommendation(db, device_id)
    
    result = {
        "deviceId": device_id,
        "timestamp": hourly.timestamp.isoformat() if hourly and hourly.timestamp else None,
        "period": hourly.period if hourly and hourly.period else None,
        "averagePm": json.loads(daily.average_pm) if daily and daily.average_pm else [],
        "averageCleanTime": json.loads(daily.average_clean_time) if daily and daily.average_clean_time else [],
        "averageCleanAmount": json.loads(daily.average_clean_amount) if daily and daily.average_clean_amount else [],
        "recommendations": json.loads(reco.recommendations) if reco and reco.recommendations else []
    }
    
    logger.info("Loaded JSON data: %s", result)
    return result