from pydantic import BaseModel

from typing import Optional

class MakePrediction(BaseModel):
    text: str
    html: bool = False

class Rating(BaseModel):
    translated_text: str
    model_id: int
    rating: bool

class GetRating(Rating):
    pass

class AddRating(Rating):
    pass

class Model(BaseModel):
    name: str
    language: str
    type: str
    train_data: Optional[str] = None
    path: str
    tokenizer: str

class GetModel(Model):
    pass

class AddModel(Model):
    pass