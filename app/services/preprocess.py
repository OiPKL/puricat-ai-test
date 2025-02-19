import logging
from datetime import datetime, timezone, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from app.database.crud import get_device, create_device, update_hourly_data, update_daily_data

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def process_hourly_post(db: Session, data: dict, device_id: int):
    logger.info("Processing HOURLY POST data for device_id: %s", device_id)
    try:
        device = get_device(db, device_id)
        if not device:
            create_device(db, device_id)

        pm_current = data.get("pmCurrent")
        current_time = datetime.now(timezone.utc)

        update_hourly_data(db, device_id, current_time, pm_current, None)

    except Exception as e:
        logger.error("Error processing HOURLY POST data for device_id %s: %s", device_id, str(e))
        raise e

def process_daily_post(db: Session, data: dict, device_id: int):
    logger.info("Processing DAILY POST data for device_id: %s", device_id)
    try:
        device = get_device(db, device_id)
        if not device:
            create_device(db, device_id)
            
        pm_current = data.get("pmCurrent")
        current_time = datetime.now(timezone.utc)
        clean_logs = data.get("CleanLog", [])
        sensor_archive = data.get("SensorArchive", [])

        period_str = get_period_str(clean_logs, current_time)
        update_hourly_data(db, device_id, current_time, pm_current, period_str)

        last_week_clean_time, this_week_clean_time, last_week_clean_amount, this_week_clean_amount = process_clean_log(clean_logs, sensor_archive)
        last_week_pm, this_week_pm = process_sensor_archive(sensor_archive)

        average_pm = [last_week_pm, this_week_pm]
        average_clean_time = [last_week_clean_time, this_week_clean_time]
        average_clean_amount = [last_week_clean_amount, this_week_clean_amount]

        update_daily_data(db, device_id, average_pm, average_clean_time, average_clean_amount)
        logger.info("DAILY POST processing completed for device_id: %s", device_id)

    except Exception as e:
        logger.error("Error processing DAILY POST data for device_id %s: %s", device_id, str(e))
        db.rollback()
        raise e

def get_period_str(clean_logs, current_time):
    """
    period : YYYY-MM-DD ~ YYYY-MM-DD
    데이터X : period = null
    2주일치 : period = (yesterday-13) ~ yesterday
    1주일치 : period = (yesterday-6) ~ yesterday
    """
    yesterday = current_time.date() - timedelta(days=1)
    if clean_logs:
        created_dates = [datetime.fromisoformat(log["createdAt"]) for log in clean_logs]
        earliest = min(created_dates)
        if earliest.date() <= yesterday - timedelta(days=13):
            return f"{(yesterday - timedelta(days=13)).strftime('%Y-%m-%d')} ~ {yesterday.strftime('%Y-%m-%d')}"
        elif earliest.date() <= yesterday - timedelta(days=6):
            return f"{(yesterday - timedelta(days=6)).strftime('%Y-%m-%d')} ~ {yesterday.strftime('%Y-%m-%d')}"
    return f"{current_time.strftime('%Y-%m-%d')} ~ {current_time.strftime('%Y-%m-%d')}"

def process_clean_log(clean_logs, sensor_archive):
    """
    CleanLog :
        - 날짜별로 지속시간(시간 단위) 합산
        - 날짜별로 총 공기정화량 합산 (dustLevelBefore - dustLevelAfter)
        - 기준 날짜(ref_date)는 sensor_archive의 마지막 recordAt를 사용
    """
    if not clean_logs:
        return [0] * 7, [0] * 7, [0] * 7, [0] * 7
    if sensor_archive:
        ref_date = max(datetime.fromisoformat(rec["recordAt"]) for rec in sensor_archive).date()

    df_clean = pd.DataFrame(clean_logs)
    df_clean["startedAt"] = pd.to_datetime(df_clean["startedAt"])
    df_clean["finishedAt"] = pd.to_datetime(df_clean["finishedAt"])
    df_clean["duration"] = (df_clean["finishedAt"] - df_clean["startedAt"]).dt.total_seconds() / 3600
    df_clean["clean_amount"] = df_clean["dustLevelBefore"] - df_clean["dustLevelAfter"]
    grouped_clean = df_clean.groupby(df_clean["startedAt"].dt.date).agg(
        total_clean_time=("duration", "sum"),
        total_clean_amount=("clean_amount", "sum")
    )
    last_week_clean_time, this_week_clean_time = [0] * 7, [0] * 7
    last_week_clean_amount, this_week_clean_amount = [0] * 7, [0] * 7
    for date, row in grouped_clean.iterrows():
        weekday = date.weekday()
        if date >= ref_date - timedelta(days=6):
            this_week_clean_time[weekday] = int(round(row['total_clean_time']))
            this_week_clean_amount[weekday] = int(round(row['total_clean_amount']))
        else:
            last_week_clean_time[weekday] = int(round(row['total_clean_time']))
            last_week_clean_amount[weekday] = int(round(row['total_clean_amount']))
    return last_week_clean_time, this_week_clean_time, last_week_clean_amount, this_week_clean_amount

def process_sensor_archive(sensor_archive):
    """
    SensorArchive :
        - 날짜별 미세먼지 평균 (소수점 1자리)
        - 기준 날짜(ref_date)는 sensor_archive의 마지막 recordAt를 사용
    """
    if not sensor_archive:
        return [0] * 7, [0] * 7

    ref_date = max(datetime.fromisoformat(rec["recordAt"]) for rec in sensor_archive).date()
    df_sensor = pd.DataFrame(sensor_archive)
    df_sensor["recordAt"] = pd.to_datetime(df_sensor["recordAt"])
    grouped_sensor = df_sensor.groupby(df_sensor["recordAt"].dt.date)["pm"].mean().round(1)
    last_week_pm, this_week_pm = [0] * 7, [0] * 7
    for date, avg_pm in grouped_sensor.items():
        weekday = date.weekday()
        if date >= ref_date - timedelta(days=6):
            this_week_pm[weekday] = avg_pm
        else:
            last_week_pm[weekday] = avg_pm
    return last_week_pm, this_week_pm