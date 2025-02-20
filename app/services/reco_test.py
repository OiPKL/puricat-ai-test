import logging
from sqlalchemy.orm import Session
from app.database.crud import update_recommendation

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def recommendation_test(db: Session, device_id: int):
    recommendations = [
        "현재 미세미먼지 농도는 8.7로, 이번 주 평균 농 도보다 덜 높습니다.",
        "이번주평균미세먼지 농도는 12.5로, 저번주 평균 미세먼지 농도 9 대비 약 36% 증가했습니다.",
        "이번주총공기정 화시간은 26시간으로, 저번주와 비슷한 수준입니다.",
        "이번주 총공기정 화량은 66 9로, 저 번주 총 공기정화량인 653에 대비 2% 증가했습니다."
    ]
    logger.info("Adding dummy recommendations for device_id: %s", device_id)
    updated_reco = update_recommendation(db, device_id, recommendations)
    return updated_reco
