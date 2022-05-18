from fastapi import FastAPI, status, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from . import tables
from . import schemas
from .database import get_db
from transformers import AutoModelForTokenClassification, AutoConfig, AutoTokenizer, AutoModelForSeq2SeqLM
from .utils import get_ner_tags, label2id, id2label, get_rebel_rel_preds

## uvicorn main:app --reload

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.get('/')
def root():
    return {'message': 'Hello World'}

@app.get("/models")
def get_model_list(db: Session = Depends(get_db)):

    models_list = db.query(tables.Model).all()
    return models_list

@app.post("/models")
def add_model(model: schemas.AddModel, db: Session = Depends(get_db)):

    new_model = tables.Model(**model.dict())
    db.add(new_model)
    db.commit()
    db.refresh(new_model)

    return {new_model}

@app.delete("/models")
def del_models( db: Session = Depends(get_db) ):
    db.query(tables.Model).delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/models/ner")
def get_model_list(db: Session = Depends(get_db)):

    models_list = db.query(tables.Model).where(tables.Model.type == "NER").all()
    return models_list

@app.delete("/models/ner")
def del_models( db: Session = Depends(get_db) ):
    db.query(tables.Model).where(tables.Model.type == "NER").delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/models/ner/all/ratings")
def get_rating(db: Session = Depends(get_db)):

    ratings = db.query(tables.Rating).all()
    return ratings

@app.get("/models/id/{model_id}")
def get_model(model_id: int, db: Session = Depends(get_db)):
    user = db.query(tables.Model).filter(tables.Model.id == model_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {model_id} does not exist")
    return {user}

@app.delete("/models/id/{model_id}")
def get_model(model_id: int, db: Session = Depends(get_db)):
    user = db.query(tables.Model).filter(tables.Model.id == model_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {model_id} does not exist")
    else:
        db.query(tables.Model).where(tables.Model.id == model_id).delete(synchronize_session=False)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/models/ner/{model_id}/ratings")
def get_rating(model_id: int, db: Session = Depends(get_db)):

    user = db.query(tables.Model).filter(tables.Model.id == model_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {model_id} does not exist")
    else:
        ratings = db.query(tables.Rating).filter(tables.Rating.model_id == model_id).all()
        return ratings


@app.post("/models/ner/{model_id}/ratings")
def post_rating(model_id: int, rating: schemas.AddRating, db: Session = Depends(get_db)):
    user = db.query(tables.Model).filter(tables.Model.id == model_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {model_id} does not exist")
    else:
        new_rating = tables.Rating(**rating.dict())
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
        return {new_rating}

@app.post("/models/ner/{model_id}/prediction")
def make_prediction(model_id: int, text_to_translate: schemas.MakePrediction, db: Session = Depends(get_db)):
    model_details = db.query(tables.Model).filter(tables.Model.id == model_id).first()
    if not model_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Model with id: {model_id} does not exist")

    path, tokenizer_path = model_details.path, model_details.tokenizer
    if (not path) or (not tokenizer_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Unable to find model of id {model_id}")
   

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, use_fast=True)
    config = AutoConfig.from_pretrained(path, label2id = label2id,  id2label=id2label)
    model = AutoModelForTokenClassification.from_pretrained(path, config = config).to("cpu")

    res = get_ner_tags(text_to_translate.text, model, tokenizer, model_details.name, text_to_translate.html)
    del tokenizer
    del config
    del model

    res["model_name"] = model_details.name
    # res["model_lang"] = model_details.language
    res["model_id"] = model_details.id
    res["text"] = text_to_translate.text

    return res

@app.post("/models/rel/{model_id}/prediction")
def get_prediction(model_id: int, text_to_translate: schemas.MakePrediction, db: Session = Depends(get_db)):
    
    model_details = db.query(tables.Model).filter(tables.Model.id == model_id).first()
    if not model_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Model with id: {model_id} does not exist")

    path, tokenizer_path = model_details.path, model_details.tokenizer
    if (not path) or (not tokenizer_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Unable to find model of id {model_id}")

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(path)

    # tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
    # model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")
    print("I am loading ...")
    res = get_rebel_rel_preds(text_to_translate.text, tokenizer, model)

    del tokenizer
    del model

    return {"prediction": res, "model_name": model_details.name,
            "model_id": model_details.id, "text": text_to_translate.text}

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



@app.get("/models/rel")
def get_model_list(db: Session = Depends(get_db)):

    models_list = db.query(tables.Model).where(tables.Model.type == "REL").all()
    return models_list

@app.delete("/models/rel")
def del_models( db: Session = Depends(get_db) ):
    db.query(tables.Model).where(tables.Model.type == "REL").delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)



@app.post("/rel/en/test/6")
def get_relations(text_to_translate: schemas.MakePrediction):
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
def get_relations(text_to_translate: schemas.MakePrediction):
    relations = []
    
    res = dict([("result", relations), 
                ("model_id", text_to_translate.model_type), 
                ("text", text_to_translate.text_to_translate)])
    
    return {"message": res}