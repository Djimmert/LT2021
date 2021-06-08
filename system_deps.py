#!/usr/bin/python3
# This scripts ...
# Authors: Jasper Bos (s3794687); Djim C. Casander (s3162753); Esther Ploeger (s3798461)
# Date:    June 8th, 2021

import requests
import spacy

nlp = spacy.load("en_core_web_md")


def get_question_type(input_q):
    """
    Performs linguistic analysis to determine question type
    :param input_q: input question, plain text (str)
    :return: question type, abbreviation (str)
    """
    # Define keywords
    duration_keywords = ['long', 'duration', 'minutes', 'time', 'length']
    time_keywords = ['century', 'year', 'when', 'month']
    location_keywords = ['country', 'location', 'where', 'coordinates']

    # Extract sentence structure
    parse = nlp(input_q)
    lemmas = []
    pos = []
    dep = []
    for word in parse:
        lemmas.append(word.lemma_)
        pos.append(word.pos_)
        dep.append(word.dep_)

    sent = parse.text.replace("?", "")  # Strip question mark
    sent = sent.replace('"', "")  # Strip double apostrophe
    sent = sent.replace("'", "")  # Strip single apostrophe

    question_type = ""
    for rel in dep:
        if 'pass' in rel:
            question_type = "passive"  # e.g. 'Which movies are directed by X?'
            break
        elif any(item in duration_keywords for item in lemmas):
            question_type = "duration"  # e.g. 'How long is X?'
        elif any(item in location_keywords for item in lemmas):
            question_type = "location"  # e.g. 'Where was X filmed?'
        elif any(item in time_keywords for item in lemmas):
            question_type = "time"  # e.g. 'When was X published?'
        elif parse[0].text.lower() == "what" or parse[0].text.lower() == "which":
            if parse[1].pos_ == "NOUN":
                if "VERB" in pos:
                    if "AUX" in pos and lemmas[pos.index("AUX")] == "be":
                        question_type = "what_A_is_X_Y"  # e.g 'What book is X based on?'
                    elif "AUX" in pos and lemmas[pos.index("VERB")] == "earn":
                        question_type = "what_A_is_X_Y"  # e.g. 'Which movies earned X an award?'
                    else:
                        question_type = "what_which_verb" # e.g. 'What awards did X receive?'
                else:
                    question_type = "whatXisY"  # e.g. 'What genre is X?'
            elif 'about' in lemmas:
                question_type = "about"
            else:
                question_type = "what_is_Xs_Y"  # e.g. 'What is X's hair color?'
        elif "tall" in lemmas:
            question_type = "tall"  # e.g 'How tall is X?'
        elif "many" in lemmas and "follower" not in lemmas and "cost" not in lemmas:  # e.g. 'How many X films are there?'
            question_type = "count"
        elif "cost" in lemmas:
            question_type = "cost"  # e.g. 'How much did X cost to make?'
        else:
            if 'pobj' in rel:
                question_type = "XofY"  # e.g. 'Who is the director of X?'
            if 'dobj' in rel:
                question_type = "verb_prop"  # e.g. 'Who directed X?'

    if not question_type:
        print("Question type could not be found ...")
    else:
        return question_type


def get_entity_property_deps(parse, question_type):
    """
    Determine and clean entity and property from question type and parse.

    :param parse: nlp parse of input question
    :question_type: abbreviation of question type (str)
    """

    # Init ent and prop
    ent = []
    prop = []

    # Extract sentence structure
    lemmas = []
    pos = []
    dep = []
    for word in parse:
        lemmas.append(word.lemma_)
        pos.append(word.pos_)
        dep.append(word.dep_)

    sent = parse.text.replace("?", "")  # Strip question mark
    sent = sent.replace('"', "")  # Strip double apostrophe
    sent = sent.replace("'", "")  # Strip single apostrophe

    if question_type == "XofY":
        # Property: from AUX to ADP
        if pos.count("ADP") == 1:
            try:
                prop = lemmas[pos.index('AUX') + 1:pos.index('ADP')]
                if len(prop) > 1:
                    if "the" in prop:  # strip 'the'
                        prop.remove("the")
                    if "a" in prop:  # strip 'a'
                        prop.remove("a")
                    if "an" in prop:  # strip 'an'
                        prop.remove("an")
            except ValueError:  # 'AUX' not in list
                print('[!] AUX not in list ?? lemmas[pos.index(AUX) + 1:pos.index(ADP)]')
                pass

            # Perhaps there is an 'of' in the entity, such as in 'Lord of the Rings'
            else:
                try:
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
                except:
                    print('[!] AUX not in list ?? lemmas[pos.index(AUX) + 1:pos.index(PROPN)]')

        ent = sent.split(" ")[pos.index('ADP') + 1:]  # assuming it always ends with '?'

    elif question_type == "verb_prop":
        # Find entity: direct object (phrase!)
        for word in parse:
            if word.dep_ == 'dobj':
                ent = phrase(word)

        main_verb = parse[dep.index("ROOT")]
        prop = [main_verb.lemma_]

    elif question_type == "duration":
        prop = {'P2047': 'duration'}
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
    elif question_type == "location":
        # Find entity using Falcon
        # Filter property answers based on answer type using VALUES
        pass
    elif question_type == "time":
        # Find entity using Falcon
        # Filter property answers based on data type of answer using VALUES
        pass
    elif question_type == "what_A_is_X_Y":
        # Find entity using Falcon
        # Find property: probably last two words of sentence (parse[-4:-2])
        prop = parse[-4:-2].text.split(" ")
    elif question_type == "what_which_verb":
        # Find entity
        # Find property: probably second word (parse[1])
        prop = [lemmas[1]]
    elif question_type == "whatXisY":
        # Find entity
        # Find property: probably words between first word and POS:AUX
        prop = parse[1:pos.index("AUX")].text.split(" ")
    elif question_type == "about":
        # Find entity
        prop = ["main", "subject"]
    elif question_type == "what_is_Xs_Y":
        # Find entity: Either between POS:AUX (lemmas[2]) and 's, or:
        #              istitle()
        if "'s" in lemmas:
            prop = lemmas[2:lemmas.index("'s")]
        else:
            prop = []
            for word in lemmas:
                if word.istitle():
                    prop.append(word)
       # Find property: probably last two words of sentence (parse[-4:-2])
        prop = parse[-4:-2].text.split(" ")

    elif question_type == "tall":
        prop = {'P2048': 'height'}
    elif question_type == "count":
        pass
    elif question_type == "cost":
        prop = {'P2130': 'cost'}

    else:
        pass

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

    ent, prop = retrieve_id_label(ent, prop)
    return ent, prop


def phrase(word):
    """
    Returns a list of the full phrase, derived from a word.
    This was copied (but slightly modified) from examples above.
    """

    return [child.text for child in word.subtree]


def retrieve_id_label(ent, prop):
    url = 'https://www.wikidata.org/w/api.php'

    params_prop = {'action': 'wbsearchentities',
                   'language': 'en',
                   'format': 'json',
                   'type': 'property'}

    params_ent = {'action': 'wbsearchentities',
                  'language': 'en',
                  'format': 'json',
                  'type': 'item'}

    if prop:
        # Find property in Wikidata
        params_prop['search'] = prop
        try:
            json_p = requests.get(url, params_prop).json()
            prop = {json_p['search'][0]['id']: json_p['search'][0]['label']}
        except IndexError:  # No result
            prop = dict()  # Empty dict
    else:
        prop = dict()  # Empty dict

    if ent:
        # Find entity in Wikidata
        params_ent['search'] = ent
        try:
            json_e = requests.get(url, params_ent).json()
            ent = {json_e['search'][0]['id']: json_e['search'][0]['label']}

        except IndexError:  # No result
            ent = dict()  # Empty dict
    else:
        ent = dict()  # Empty dict

    return ent, prop
