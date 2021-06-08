#!/usr/bin/python3
# This scripts ...
# Authors: Jasper Bos (s3794687); Jim Casander (s3162753); Esther Ploeger (s3798461)
# Date:    June 8th, 2021

import requests
import spacy
import sys
import json

nlp = spacy.load("en_core_web_md")
nlp.add_pipe("entityLinker", last=True)


def call_falcon(q):
    """
    Calls the Falcon 2.0 API to identify the relations and entities of Wikidata in q.
    :param q: question (str)
    :return: dicts of entities and relations where key: id and value: label
    """
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    url = 'https://labs.tib.eu/falcon/falcon2/api?mode=long'
    q = q.replace("'", '')  # Avoid conflict in payload
    q = q.replace('"', '')  # Avoid conflict in payload
    q = q.replace('movie', '')  # Improve performance
    q = q.replace('film', '')  # Improve performance
    payload = '{"text":"' + q + '"}'
    r = requests.post(url, data=payload.encode('utf-8'), headers=headers)
    if r.status_code == 200:  # OK
        response = r.json()
        entities = {result[0].split('/')[-1][:-1]: result[1] for result in response['entities_wikidata']}
        relations = {result[0].split('/')[-1][:-1]: result[1] for result in response['relations_wikidata']}
        return entities, relations
    else:
        print(q, file=sys.stderr)
        print("Falcon 2.0 API error: status {}".format(r.status_code), file=sys.stderr)
        return dict(), dict()


def call_entitylinker(q):
    """
    Uses Spacy Entity Linker to identify the entities of Wikidata in q.
    :param q: question (str)
    :return: dict of entities and relations where key: id and value: label
    """

    doc = nlp(q)
    return {'Q' + str(ent.get_id()): ent.get_label() for ent in doc._.linkedEntities}


def get_entities_properties_libs(q):
    """
    Uses Spacy Entity Linker anc Falcon2.0 to identify the entities of Wikidata in q.
    :param q: question (str)
    :return: dicts of entities and relations where key: id and value: label
    """
    entities1, relations = call_falcon(q)
    return {**entities1, **call_entitylinker(q)}, relations