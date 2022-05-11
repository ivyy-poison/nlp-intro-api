from prompt_toolkit import HTML
from pydantic import BaseModel
from typing import Optional
from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import psycopg2
from psycopg2.extras import RealDictCursor
import time

from .config import settings


## uvicorn main:app --reload

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)




while True:
    try:
        conn = psycopg2.connect(host=settings.db_host, database=settings.db_name, user=settings.db_user,
                               password=settings.db_password, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print("database connection successful")
        break
    except Exception as error:
        print("database connection failed")
        print("error:", error)
        time.sleep(2)





class TextToTranslate(BaseModel):
    text_to_translate: str
    model_type: str
    html: bool = False
    rating: Optional[int] = None

class Rating(BaseModel):
    translated_text: str
    model_id: int
    rating: bool

class Model(BaseModel):
    name: str
    language: str
    type: str
    train_data: Optional[str] = None

from fastapi.params import Body

@app.get('/')
def root():
    return {'message': 'Hello World ssss'}

@app.get("/ner/models")
def get_model_list():
    cursor.execute(""" SELECT * FROM models WHERE type='NER' """)
    res = cursor.fetchall()
    return {"message": res}

@app.post("/ner/models")
def add_model(model: Model):
    cursor.execute(""" INSERT INTO MODELS (NAME, LANGUAGE, TYPE, TRAIN_DATA) VALUES
                    (%s, %s, %s, %s) RETURNING * """, 
                    (model.name, model.language, model.type, model.train_data) )
    res=cursor.fetchone()
    conn.commit()
    return {"message": res}

@app.get("/ner/models/{model_id}")
def get_model(model_id: int):
    cursor.execute(""" SELECT * FROM models WHERE type='NER' AND id = %s """, (str(model_id),))
    res = cursor.fetchone()
    return {"message": res}


@app.get("/ner/models/{model_id}/ratings")
def get_rating(model_id: int):
    cursor.execute("""SELECT * FROM models WHERE id = %s """, (str(model_id), ))
    if not cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"model with id: {model_id} not found")
    else:
        cursor.execute("""SELECT * FROM RATINGS WHERE model_id = %s """, (str(model_id), ))
        res = cursor.fetchall()
        return {"message": res}

@app.post("/ner/models/{model_id}/ratings")
def post_rating(model_id: int, rating: Rating):
    cursor.execute("""SELECT * FROM models WHERE id = %s """, (str(model_id), ))
    if not cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"model with id: {model_id} not found")
    else:
        cursor.execute("""INSERT INTO RATINGS (model_id, translated_text, rating) 
                        VALUES (%s, %s, %s) RETURNING * """,
                        (rating.model_id, rating.translated_text, rating.rating) )
        new_post = cursor.fetchone()
        conn.commit()
        return {"message": new_post}

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