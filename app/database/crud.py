import json
import logging
from sqlalchemy.orm import Session
from app.database.models import Device, HourlyData, DailyData, Recommendation

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def create_device(db: Session, device_id: int):
    logger.info("Creating device with device_id: %s", device_id)
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if device:
        logger.info("Device %s already exists", device_id)
        return device
    
    try:
        device = Device(device_id=device_id)
        hourly = HourlyData(device_id=device_id, timestamp=None, period=None, pm_current=None)
        daily = DailyData(device_id=device_id)
        reco = Recommendation(device_id=device_id)

        db.add_all([device, hourly, daily, reco])
        db.commit()
        logger.info("Device %s and related records created", device_id)
    except Exception as e:
        db.rollback()
        logger.error("Error creating device %s: %s", device_id, str(e))
        raise e

    return device

def get_device(db: Session, device_id: int):
    logger.info("Fetching device data for device_id: %s", device_id)
    return db.query(Device).filter(Device.device_id == device_id).first()

def get_hourly_data(db: Session, device_id: int):
    logger.info("Fetching hourly data for device_id: %s", device_id)
    return db.query(HourlyData).filter(HourlyData.device_id == device_id).first()

def get_daily_data(db: Session, device_id: int):
    logger.info("Fetching daily data for device_id: %s", device_id)
    return db.query(DailyData).filter(DailyData.device_id == device_id).first()

def get_recommendation(db: Session, device_id: int):
    logger.info("Fetching recommendation for device_id: %s", device_id)
    return db.query(Recommendation).filter(Recommendation.device_id == device_id).first()

def update_hourly_data(db: Session, device_id: int, timestamp, pm_current: float, period=None):
    logger.info("Updating hourly data for device_id: %s", device_id)
    hourly = db.query(HourlyData).filter(HourlyData.device_id == device_id).first()
    if not hourly:
        logger.info("Hourly data for device_id %s not found", device_id)
        return None
    
    try:
        hourly.timestamp = timestamp
        hourly.pm_current = pm_current

        if period is not None:
            hourly.period = period

        db.commit()
        logger.info("Hourly data for device_id %s updated", device_id)
    except Exception as e:
        db.rollback()
        logger.error("Error updating hourly data for device_id %s: %s", device_id, str(e))
        raise e
    
    return hourly

def update_daily_data(db: Session, device_id: int, average_pm, average_clean_time, average_clean_amount):
    logger.info("Updating daily data for device_id: %s", device_id)
    daily = db.query(DailyData).filter(DailyData.device_id == device_id).first()
    if not daily:
        logger.info("Daily data for device_id %s not found", device_id)
        return None

    try:
        daily.average_pm = json.dumps(average_pm)
        daily.average_clean_time = json.dumps(average_clean_time)
        daily.average_clean_amount = json.dumps(average_clean_amount)

        db.commit()
        logger.info("Daily data for device_id %s updated", device_id)
    except Exception as e:
        db.rollback()
        logger.error("Error updating daily data for device_id %s: %s", device_id, str(e))
        raise e

    return daily

def update_recommendation(db: Session, device_id: int, recommendations):
    logger.info("Updating recommendation for device_id: %s", device_id)
    reco = db.query(Recommendation).filter(Recommendation.device_id == device_id).first()
    if not reco:
        logger.info("Recommendation for device_id %s not found", device_id)
        return None

    try:
        reco.recommendations = json.dumps(recommendations)
        db.commit()
        logger.info("Recommendation for device_id %s updated", device_id)
    except Exception as e:
        db.rollback()
        logger.error("Error updating recommendation for device_id %s: %s", device_id, str(e))
        raise e

    return reco
