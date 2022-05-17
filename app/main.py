from prompt_toolkit import HTML
from pydantic import BaseModel
from typing import Optional
from fastapi import FastAPI, status, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware

import psycopg2
from psycopg2.extras import RealDictCursor
import time

from sqlalchemy.orm import Session
from sqlalchemy import delete
from . import models
from .database import engine, get_db
from .config import settings
from transformers import AutoModelForTokenClassification, AutoConfig, AutoTokenizer
from .utils import get_ner_tags, label2id, id2label

## uvicorn main:app --reload

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

class TextToTranslate(BaseModel):
    text: str
    html: bool = False

class Rating(BaseModel):
    translated_text: str
    model_id: int
    rating: bool

class Model(BaseModel):
    name: str
    language: str
    type: str
    train_data: Optional[str] = None
    path: str
    tokenizer: str

from fastapi.params import Body

@app.get('/')
def root():
    return {'message': 'Hello World ss'}

# "/usr/src/app/models/BERT_Chinese_ZH/checkpoint-33753"

@app.get("/ner/models")
def get_model_list(db: Session = Depends(get_db)):

    models_list = db.query(models.Model).all()
    return models_list


@app.post("/ner/models")
def add_model(model: Model, db: Session = Depends(get_db)):

    new_model = models.Model(**model.dict())
    db.add(new_model)
    db.commit()
    db.refresh(new_model)

    return {new_model}

@app.delete("/ner/models")
def del_models( db: Session = Depends(get_db) ):
    db.query(models.Model).delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/ner/models/{model_id}")
def get_model(model_id: int, db: Session = Depends(get_db)):
    user = db.query(models.Model).filter(models.Model.id == model_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {model_id} does not exist")
    return {user}

@app.delete("/ner/models/{model_id}")
def get_model(model_id: int, db: Session = Depends(get_db)):
    user = db.query(models.Model).filter(models.Model.id == model_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {model_id} does not exist")
    else:
        db.query(models.Model).where(models.Model.id == model_id).delete(synchronize_session=False)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/ner/models/{model_id}/ratings")
def get_rating(model_id: int, db: Session = Depends(get_db)):

    user = db.query(models.Model).filter(models.Model.id == model_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {model_id} does not exist")
    else:
        ratings = db.query(models.Rating).filter(models.Rating.model_id == model_id).all()
        return ratings


@app.post("/ner/models/{model_id}/ratings")
def post_rating(model_id: int, rating: Rating, db: Session = Depends(get_db)):
    user = db.query(models.Model).filter(models.Model.id == model_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {model_id} does not exist")
    else:
        new_rating = models.Rating(**rating.dict())
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
        return {new_rating}

@app.post("/ner/models/{model_id}/prediction")
def make_prediction(model_id: int, text_to_translate: TextToTranslate, db: Session = Depends(get_db)):
    user = db.query(models.Model).filter(models.Model.id == model_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Model with id: {model_id} does not exist")

    path, tokenizer_path = user.path, user.tokenizer
    if (not path) or (not tokenizer_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Unable to find model of id {model_id}")
   

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, use_fast=True)
    config = AutoConfig.from_pretrained(path, label2id = label2id,  id2label=id2label)
    model = AutoModelForTokenClassification.from_pretrained(path, config = config).to("cpu")

    res = get_ner_tags(text_to_translate.text, model, tokenizer, user.name, text_to_translate.html)
    del tokenizer
    del config
    del model

    return res

# @app.get("/ner/models/{model_id}/ratings/{rating_id}")
# def get_rating(model_id: int, rating_id: int):
#     cursor.execute("""SELECT * FROM models WHERE id = %s """, (str(model_id), ))
#     if not cursor.fetchone():
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail=f"model with id: {model_id} not found")
#     else:
#         cursor.execute("""SELECT * FROM RATINGS WHERE model_id = %s AND id = %s """, (str(model_id), str(rating_id)))
#         res = cursor.fetchall()
#         return {"message": res}

## Will I require delete and update HTTP Requests? Delete a single rating, delete all ratings
## from a particular model, update a single rating

## will I require deleting and posting of new models into model table? 

@app.post("/ner/zh/test/2")
def translate_text(text_to_translate: TextToTranslate):

    html = """
      <h2 style="margin: 0">what's the title ONE</h2>

      <div class="entities" style="line-height: 2.5; direction: ltr">1966
      <mark class="entity" style="background: #bfe1d9; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
          年2月出生，
          <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; text-transform: uppercase; vertical-align: middle; margin-left: 0.5rem">DATE</span>
      </mark>

      <mark class="entity" style="background: #ff9561; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
          汉族
          <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; text-transform: uppercase; vertical-align: middle; margin-left: 0.5rem">LOC</span>
      </mark>
      ，本科学历，陕西咸阳人，</div>
    """
    
    res = dict([("html", html), ("model_id", text_to_translate.model_type), ("text", text_to_translate.text_to_translate)])
    
    return {"message": res}

@app.post("/ner/zh/test/1")
def translate_text(text_to_translate: TextToTranslate):

    html = """
          <h2 style="margin: 0">what's the title TWO</h2>

      <div class="entities" style="line-height: 2.5; direction: ltr">1966
      <mark class="entity" style="background: #bfe1d9; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
          年2月出生，
          <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; text-transform: uppercase; vertical-align: middle; margin-left: 0.5rem">DATE</span>
      </mark>

      <mark class="entity" style="background: #ff9561; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
          汉族
          <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; text-transform: uppercase; vertical-align: middle; margin-left: 0.5rem">LOC</span>
      </mark>
      ，本科学历，陕西咸阳人，</div>

    """

    res = dict([("html", html), ("model_id", text_to_translate.model_type), ("text", text_to_translate.text_to_translate)])


    
    return {"message": res}

@app.post("/ner/zh/test/3")
def translate_text(text_to_translate: TextToTranslate):

    html = """
      <h2 style="margin: 0">what's the title THREE</h2>

      <div class="entities" style="line-height: 2.5; direction: ltr">1966
      <mark class="entity" style="background: #bfe1d9; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
          年2月出生，
          <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; text-transform: uppercase; vertical-align: middle; margin-left: 0.5rem">DATE</span>
      </mark>

      <mark class="entity" style="background: #ff9561; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
          汉族
          <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; text-transform: uppercase; vertical-align: middle; margin-left: 0.5rem">LOC</span>
      </mark>
      ，本科学历，陕西咸阳人，</div>
    """

    res = dict([("html", html), ("model_id", text_to_translate.model_type), ("text", text_to_translate.text_to_translate)])

    return {'message': res}










@app.get("/re/models")
def get_model_list():
    cursor.execute(""" SELECT * FROM models WHERE type='RE' """)
    res = cursor.fetchall()
    return {"message": res}

@app.post("/rel/en/test/6")
def get_relations(text_to_translate: TextToTranslate):
    relations = [('Dune', 'genre', 'science fiction film'),
                ('Denis Villeneuve', 'genre', 'science fiction film'),
                ('Dune', 'director', 'Denis Villeneuve'),
                ('Dune', 'screenwriter', 'Jon Spaihts'),
                ('Dune', 'screenwriter', 'Eric Roth'),
                ('Dune', 'publication date', '2021')]
    
    res = dict([("result", relations), 
                ("model_id", text_to_translate.model_type), 
                ("text", text_to_translate.text_to_translate)])


    return {"message": res}

@app.post("/rel/en/test/5")
def get_relations(text_to_translate: TextToTranslate):
    relations = []
    
    res = dict([("result", relations), 
                ("model_id", text_to_translate.model_type), 
                ("text", text_to_translate.text_to_translate)])
    
    return {"message": res}