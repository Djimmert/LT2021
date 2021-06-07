#!/usr/bin/python3
# This scripts ...
# Authors: Jasper Bos (s3794687); Jim Casander (s3162753); Esther Ploeger (s3798461)
# Date:    June 8th, 2021

import argparse
import requests
import csv
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


def get_entities_properties(q):
    """
    Uses Spacy Entity Linker anc Falcon2.0 to identify the entities of Wikidata in q.
    :param q: question (str)
    :return: dicts of entities and relations where key: id and value: label
    """
    entities1, relations = call_falcon(q)
    return entities1 | call_entitylinker(q), relations


def check_keywords(q):
    q = q.lower()
    if 'cult - like church' in q:
        return {'P140': 'religion'}
    elif 'named' in q and 'after' in q:
        return {'P138': 'named after'}
    elif 'film' in q and 'location' in q or 'where' in q and 'film' in q or 'film' in q and 'country' in q or 'film' in q and 'city' in q or 'film' in q and 'place' in q:
        return {'P915': 'filming location'}
    elif 'can' in q and 'watch' in q:
        return {'P750': 'distributed by'}
    elif 'compan' in q and 'direct' in q or 'compan' in q and 'produce' in q:
        return {'P272': 'production company'}
    elif 'how long' in q:
        return {'P2047': 'duration'}
    elif 'cost' in q:
        return {'P2130': 'cost'}
    elif 'box office' in q:
        return {'P2142': 'box office'}
    elif 'tall' in q.split():
        return {'P2048': 'height'}
    elif 'publicised' in q or 'released' in q or 'come out' in q:
        return {'P577': 'publication date'}
    elif 'born' in q and 'country' in q or 'born' in q and 'city' in q or 'born' in q and 'place' in q:
        return {'P19': 'place of birth'}
    elif 'when' in q and 'born' in q:
        return {'P569': 'date of birth'}
    elif 'genre' in q:
        return {'P136': 'genre'}
    elif 'main subject' in q:
        return {'P921': 'main subject'}
    elif 'original language' in q or 'language' in q and 'spoken' in q:
        return {'P364': 'original language of film or TV show'}
    elif 'cause' in q and 'death' in q or 'how' in q and 'die' in q:
        return {'P509': 'cause of death'}
    elif 'followed' in q:
        return {'P156': 'followed by'}


def retrieve_answer(q, ents, props):
    """

    """

    for entity_id in ents:
        for property_id in props:

            query = 'SELECT ?answerLabel WHERE {' + \
            'wd:' + entity_id + ' wdt:' + property_id + ' ?answer.' + \
            ' SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }' + \
            '}'

            try:
                data = requests.get('https://query.wikidata.org/sparql',
                                params={'query': query, 'format': 'json'}).json()
                if data['results']['bindings']:
                    for item in data['results']['bindings']:
                        for var in item:
                            if item[var]['value']:
                                if 'coordinate' in q:  # Answer must be coordinate
                                    if 'xml:lang' not in item[var]:
                                        print(item[var]['value'])
                                else:
                                    print(item[var]['value'])

            except json.decoder.JSONDecodeError:  # Sometimes nothing is returned
                retrieve_answer(q, [entity_id], [property_id])  # Try again



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('questionfile', help='path to .txt file with all questions')
    args = parser.parse_args()

    with open(args.questionfile, 'r', encoding="utf-16") as f:
        total = sum(1 for row in f)

    i = 1
    with open(args.questionfile, 'r', encoding="utf-16") as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            id, q = row[0], row[1]
            filter = ('film', 'movie')
            q = ' '.join([token for token in q[:-1].split() if token.lower() not in filter])

            entities, relations = get_entities_properties(q)
            if check_keywords(q):  # Overwrite
                print("[!] Property overwritten by keywords.")
                relations = check_keywords(q)
            print('Q:\t', q)
            print('E:\t', entities)
            print('R:\t', relations)
            sys.stderr.write("\r" + "Answered question " + str(i) + " of " + str(total))
            sys.stderr.flush()
            i += 1
            retrieve_answer(q, entities, relations)
            print()

if __name__ == "__main__":
    main()