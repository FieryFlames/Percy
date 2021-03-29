from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer

Base = declarative_base()

class Booster(Base):
    __tablename__ = "boosters"

    id = Column(Integer, primary_key=True)

    guild_id = Column(Integer)
    user_id = Column(Integer)
    role_id = Column(Integer)