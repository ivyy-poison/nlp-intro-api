from transformers import pipeline
from transformers import AutoModelForTokenClassification, AutoConfig
from transformers import AutoTokenizer

from spacy import displacy

id2label =  {
    0: "O",
    1: "B-PER",
    2: "I-PER",
    3: "B-ORG",
    4: "I-ORG",
    5: "B-LOC",
    6: "I-LOC",
    7: "ERR"
  }

label2id =  {
    "O": 0,
    "B-PER": 1,
    "I-PER": 2,
    "B-ORG": 3,
    "I-ORG": 4,
    "B-LOC": 5,
    "I-LOC": 6,
    "ERR": 7
}

def get_ner_tags(sequence, model, tokenizer, model_name, html=False,):
    """
    sequence: text to be parsed into model for Named Entity Recognition task
    model: fine-tuned NER model to tag named entities
    tokenizer: tokenizer used when training model
    model_name: name of the model used in prediction
    """

    ner_pipe = pipeline("ner", model = model, tokenizer = tokenizer)
    named_entity = []
    list_of_entities = []
    prev_token = None

    for token in ner_pipe(sequence):
        if prev_token is None:
            named_entity = [token]

        elif token["entity"][-3:] == prev_token["entity"][-3:] and token["index"] - prev_token["index"] == 1:
            named_entity.append(token)
        else:
            list_of_entities.append(named_entity.copy())
            named_entity = [token]
        prev_token = token

    if named_entity:
        list_of_entities.append(named_entity)


    res = {}
    res["entities"] = []

    for entity in list_of_entities:
        list_of_tokens = [token["word"] for token in entity]
        string = ''.join(list_of_tokens).replace("▁", " ").lstrip()
        res["entities"].append({"entity_name": string, "category": entity[0]["entity"][-3:], "character_span": (entity[0]["start"], entity[-1]["end"])})

    if html:
        res["html"] = get_displacy_render(sequence, res["entities"], model_name)
    
    return res


def get_displacy_render(sequence, entities, model_name):
    dict_to_render = {
        "text": sequence,
        "ents": [{"start": entity["character_span"][0], "end": entity["character_span"][1], "label": entity["category"] } for entity in entities],
        "title": f"{model_name}"
    }
    html = displacy.render(dict_to_render, style="ent", manual=True)
    return html



def extract_triplets(text):
    triplets = []
    relation, subject, relation, object_ = '', '', '', ''
    text = text.strip()
    current = 'x'
    for token in text.replace("<s>", "").replace("<pad>", "").replace("</s>", "").split():
        if token == "<triplet>":
            current = 't'
            if relation != '':
                # triplets.append({'head': subject.strip(), 'type': relation.strip(),'tail': object_.strip()})
                triplets.append((subject.strip(), relation.strip(),object_.strip()))
                relation = ''
            subject = ''
        elif token == "<subj>":
            current = 's'
            if relation != '':
                # triplets.append({'head': subject.strip(), 'type': relation.strip(),'tail': object_.strip()})
                triplets.append((subject.strip(), relation.strip(),object_.strip()))
            object_ = ''
        elif token == "<obj>":
            current = 'o'
            relation = ''
        else:
            if current == 't':
                subject += ' ' + token
            elif current == 's':
                object_ += ' ' + token
            elif current == 'o':
                relation += ' ' + token
    if subject != '' and relation != '' and object_ != '':
        # triplets.append({'head': subject.strip(), 'type': relation.strip(),'tail': object_.strip()})
        triplets.append((subject.strip(), relation.strip(),object_.strip()))
    return triplets


def get_rebel_rel_preds(sequence, tokenizer, model):
    gen_kwargs = {
      "max_length": 256,
      "length_penalty": -20,
      "num_beams": 3,
      "num_return_sequences": 3,
    }
    model_inputs = tokenizer(sequence, max_length=256, padding=True, truncation=True, return_tensors = 'pt')
    generated_tokens = model.generate(
        model_inputs["input_ids"].to(model.device),
        attention_mask=model_inputs["attention_mask"].to(model.device),
        **gen_kwargs,
    )

    # Extract text
    decoded_preds = tokenizer.batch_decode(generated_tokens, skip_special_tokens=False)

    pred_list = []

    # Extract triplets
    for idx, sentence in enumerate(decoded_preds):
        pred_list.extend(extract_triplets(sentence))
    return list(set(pred_list))