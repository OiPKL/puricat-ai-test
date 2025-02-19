import json
from sqlalchemy import Column, BigInteger, Float, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Device(Base):
    __tablename__ = 'device'
    device_id = Column(BigInteger, primary_key=True)
    hourly_data = relationship("HourlyData", back_populates="device", uselist=False)
    daily_data = relationship("DailyData", back_populates="device", uselist=False)
    recommendation = relationship("Recommendation", back_populates="device", uselist=False)

class HourlyData(Base):
    """
    매시간마다 업데이트 되는 데이터
    - POST(Hourly) : pm_current
    - sLLM 모델 추론 후 업데이트 : timestamp, period
    """
    __tablename__ = 'hourly_data'
    device_id = Column(BigInteger, ForeignKey("device.device_id"), primary_key=True, nullable=False)
    timestamp = Column(DateTime, nullable=True)
    period = Column(String, nullable=True)
    pm_current = Column(Float, nullable=True)
    device = relationship("Device", back_populates="hourly_data")

class DailyData(Base):
    """
    자정마다 업데이트 되는 데이터
    - POST(Daily) : average_pm, average_clean_time, average_clean_amount
    - 각 배열 데이터는 JSON 문자열로 저장하고, 응답 시에는 파싱하여 [[...], [...]] 형태로 반환
    """
    __tablename__ = 'daily_data'
    device_id = Column(BigInteger, ForeignKey("device.device_id"), primary_key=True, nullable=False)
    average_pm = Column(Text, nullable=False, default=lambda: json.dumps([[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]]))
    average_clean_time = Column(Text, nullable=False, default=lambda: json.dumps([[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]]))
    average_clean_amount = Column(Text, nullable=False, default=lambda: json.dumps([[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]]))
    device = relationship("Device", back_populates="daily_data")

class Recommendation(Base):
    """
    매시간마다 업데이트 되는 데이터
    - sLLM 모델 추론 후 생성되는 recommendations
    - 배열 형태의 데이터를 JSON 문자열로 저장
    """
    __tablename__ = 'recommendation'
    device_id = Column(BigInteger, ForeignKey("device.device_id"), primary_key=True, nullable=False)
    recommendations = Column(Text, nullable=False, default=lambda: json.dumps(["아직 데이터가 충분하지 않습니다..."] * 4))
    device = relationship("Device", back_populates="recommendation")