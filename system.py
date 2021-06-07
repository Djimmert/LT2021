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


def get_question_type(input_q):
    """
    Performs linguistic analysis to determine question type

    :param input_q: input question, plain text (str)
    :return: question type, abbreviation (str)
    """
    # Define keywords
    duration_keywords = ['how long', 'How long', 'duration',
                         'How many minutes', 'how many minutes',
                         'How much time', 'how much time',
                         'What is the length of', 'what is the length of']

    # Extract sentence structure
    parse = nlp(input)
    lemmas = []
    pos = []
    dep = []
    for word in parse:
        lemmas.append(word.lemma_)
        pos.append(word.pos_)
        dep.append(word.dep_)

    question_type = ""
    for rel in dep:
        if 'pass' in rel:
            question_type = "passive"  # e.g. 'Which movies are directed by X?'
            break
        else:
            if 'pobj' in rel:
                question_type = "XofY"  # e.g. 'Who is the director of X?'
            if 'dobj' in rel:
                question_type = "verb_prop"  # e.g. 'Who directed X?'

    for keyword in duration_keywords:
        if keyword in sent:
            question_type = "duration"  # e.g. 'How long is X?'

    if not question_type:
        print("Question type could not be found ...")
    else:
        return question_type


def get_entity_property(parse, question_type):
    """
    Determine and clean entity and property from question type and parse

    :param parse: nlp parse of input question
    :question type: abbreviation of question type (str)
    """
    
    if question_type == "XofY":
    
        # Property: from AUX to ADP
        if pos.count("ADP") == 1:
            prop = lemmas[pos.index('AUX') + 1:pos.index('ADP')]
            if len(prop) > 1:
                if "the" in prop:  # strip 'the'
                    prop.remove("the")
                if "a" in prop:  # strip 'a'
                    prop.remove("a")
                if "an" in prop:  # strip 'an'
                    prop.remove("an")
    
        # More than one adposition: 'of' is likely in property (e.g. 'cause of death')
        # Filter these specific common cases out manually
        else:
            if "cause of death" in parse.text:
                prop = ["cause of death"]
            elif "city of birth" in parse.text:
                prop = ["birth city"]
            elif "date of birth" in parse.text:
                prop = ["birth date"]
            elif "country of origin" in parse.text:
                prop = ["country of origin"]
            elif "country of citizenship" in parse.text:
                prop = ["country of citizenship"]
    
            # Perhaps there is an 'of' in the entity, such as in 'Lord of the Rings'
            else:
                prop = lemmas[pos.index('AUX') + 1:pos.index('PROPN')]
                if len(prop) > 1:
                    if "the" in prop:  # strip 'the'
                        prop.remove("the")
                    if "a" in prop:  # strip 'a'
                        prop.remove("a")
                    if "an" in prop:  # strip 'an'
                        prop.remove("an")
                    if "of" in prop:  # strip 'of'
                        prop.remove("of")
    
        ent = sent.split(" ")[pos.index('ADP') + 1:]  # assuming it always ends with '?'
    
    elif question_type == "verb_prop":
        # Find entity: direct object (phrase!)
        for word in parse:
            if word.dep_ == 'dobj':
                ent = phrase(word)
    
        main_verb = parse[dep.index("ROOT")]
        prop = [main_verb.lemma_]
    
    elif question_type == "duration":
        prop = ["duration"]
        # Find entity: probably follows main verb (ROOT)
        ent = sent.split(" ")[dep.index("ROOT") + 1:]
    
    elif question_type == "passive":
        for word in parse:
            if word.dep_ == 'pobj':
                ent = phrase(word)
    
        # Find prop: probably follows main verb (ROOT)
        for word in parse:
            if word.pos_ == "VERB" and word.dep_ == "ROOT":
                prop = [word.text]
    
        # Filter entity: starts with first capital letter and start is not an adjective (e.g. the Dutch movie ...)
    try:
        start = min([ent.index(word) for word in ent if word.istitle() and \
                     pos[sent.split(" ").index(word)] != "ADJ"])
        ent = ent[start:]
    except ValueError:
        pass

        # Convert entity and property from list to string
    ent = " ".join(ent)
    prop = " ".join(prop)
    
    prop = prop.replace('"', "")  # Strip double apostrophe
    prop = prop.replace("'", "")  # Strip single apostrophe
    
    return ent, prop

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
