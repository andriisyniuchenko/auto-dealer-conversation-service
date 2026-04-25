from sqlalchemy import Column, String, Integer, Float, Text

from app.core.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(String, primary_key=True)
    make = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    transmission = Column(String, nullable=False)
    mileage = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    color = Column(String, nullable=False)
    engine = Column(String, nullable=False)
    origin = Column(String, nullable=False)
    features = Column(Text, nullable=False, default="")