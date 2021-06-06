#!/usr/bin/python3
# This scripts ...
# Authors: Jasper Bos (s3794687); Jim Casander (s3162753); Esther Ploeger (s3798461)
# Date:    June 8th, 2021

import argparse
import requests
import csv
import spacy
import sys

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
    if 'cult-like church' in q:
        return 'P140'  # Religion
    elif 'named' in q and 'after' in q:
        return 'P138'  # Named after
    elif 'film' and 'location' in q or 'where' and 'film' in q or 'film' and 'country' in q or 'film' and 'city' in q or 'film' and 'place' in q:
        return 'P915'  # Filming location
    elif 'can' and 'watch' in q:
        return 'P750'
    elif 'compan' and 'direct' in q or 'compan' and 'produce' in q:
        return 'P272'
    elif 'how long' in q:
        return 'P2047'
    elif 'cost' in q:
        return 'P2130'
    elif 'box office' in q:
        return 'P2142'
    elif 'tall' in q.split():
        return 'P2142'
    elif 'publicised' in q or 'released' in q or 'come out' in q:
        return 'P577'  # Publication date
    elif 'born' and 'country' in q or 'born' and 'city' in q or 'born' and 'place' in q:
        return 'P19'  # Place of birth
    elif 'when' and 'born' in q:
        return 'P569'  # Date of birth
    elif 'genre' in q:
        return 'P136'  # Genre
    elif 'main subject' in q:
        return 'P921'  # Main subject
    elif 'original language' in q or 'language' and 'spoken' in q:
        return 'P364'  # Original language of film or TV show
    elif 'cause' and 'death' in q:
        return 'P509'


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
            entities, relations = get_entities_properties(q)
            if check_keywords(q):
                relations = check_keywords(q)
            print('Q:\t', q)
            print('E:\t', entities)
            print('R:\t', relations)
            sys.stderr.write("\r" + "Answered question " + str(i) + " of " + str(total))
            sys.stderr.flush()
            i += 1
            print()

if __name__ == "__main__":
    main()