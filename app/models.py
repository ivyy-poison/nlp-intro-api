from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP

from .database import Base

class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    language = Column(String, nullable=False)
    type = Column(String, nullable=False)
    train_data = Column(String)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))

    # published = Column(Boolean, server_default='TRUE', nullable=False)
    # owner_id = Column(Integer, ForeignKey(
    #     "users.id", ondelete="CASCADE"), nullable=False)

    # owner = relationship("User")


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, nullable=False)
    translated_text = Column(String, nullable=False)
    rating = Column(Boolean, nullable=False)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=text('now()'))
    
    model = relationship("Model")