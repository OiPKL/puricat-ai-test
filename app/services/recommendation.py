import logging
from fastapi import Request
from sqlalchemy.orm import Session
from app.models.inference import run_inference
from app.database.crud import update_recommendation

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def generate_and_update_recommendation(db: Session, device_id: int, request: Request):
    logger.info("Generating recommendation for device_id: %s", device_id)

    try:
        result = run_inference(db, device_id, request)
        recommendations = result.get("recommendations", [])

        if not recommendations:
            logger.warning("No recommendations generated for device_id: %s", device_id)
            return None

        updated_reco = update_recommendation(db, device_id, recommendations)
        if updated_reco:
            logger.info("Successfully updated recommendation for device_id: %s", device_id)
        else:
            logger.warning("Failed to update recommendation for device_id: %s", device_id)

        return updated_reco

    except Exception as e:
        logger.error("Error during recommendation generation and update for device_id %s: %s", device_id, str(e))
        raise e