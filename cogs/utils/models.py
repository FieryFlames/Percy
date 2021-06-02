from sqlalchemy import BIGINT, Column, Integer, JSON, String
from sqlalchemy.ext.declarative import declarative_base
#from sqlalchemy_json import NestedMutableJson
Base = declarative_base()


class Booster(Base):
    __tablename__ = "boosters"

    id = Column(BIGINT, primary_key=True)

    guild_id = Column(BIGINT)
    user_id = Column(BIGINT)
    role_id = Column(BIGINT, nullable=True)
    # in my testing, the longest a role name can be is 100 characters
    role_name = Column(String(100), nullable=True)
    role_color = Column(Integer, nullable=True)


#class Guild(Base):
#    id = Column(BIGINT, primary_key=True, autoincrement=False)
#    data = Column(NestedMutableJson)