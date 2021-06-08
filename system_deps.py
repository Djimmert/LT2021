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
    if lemmas[0] == "do":
        question_type = "yes/no"
    else:
        for rel in dep:
            if 'pass' in rel:
                if parse[0].text.lower() == 'by':
                    question_type = "XofY"
                else:
                    question_type = "passive"  # e.g. 'Which movies are directed by X?'
                break
            else:
                if 'pobj' in rel:
                    question_type = "XofY"  # e.g. 'Who is the director of X?'
                if 'dobj' in rel:
                    question_type = "verb_prop"  # e.g. 'Who directed X?'
        if any(item in duration_keywords for item in lemmas):
            question_type = "duration"  # e.g. 'How long is X?'
        elif any(item in location_keywords for item in lemmas):
            question_type = "location" # e.g. 'Where was X filmed?'
        elif any(item in time_keywords for item in lemmas):
            question_type = "time" # e.g. 'When was X published?'
        elif parse[0].text == "What" or parse[0].text == "Which":
            if parse[1].pos_ == "NOUN":
                if "AUX" in pos and lemmas[pos.index("AUX")] == "be":
                    question_type = "what_A_is_X_Y" # e.g 'What book is X based on?'
                elif "AUX" in pos and lemmas[pos.index("VERB")] == "earn":
                    question_type = "what_A_is_X_Y" # e.g. 'Which movies earned X an award?'
                else:
                    question_type = "what_which_verb" # e.g. 'What awards did X receive?'
            elif 'about' in lemmas:
                question_type = "about"
            else:
                question_type = "what_is_Xs_Y" # e.g. 'What is X's hair color?'
        elif "tall" in lemmas:
            question_type = "tall" # e.g 'How tall is X?'
        elif "cost" in lemmas:
            question_type = "cost" # e.g. 'How much did X cost to make?'
        elif ("many" in lemmas or "much" in lemmas) and "follower" not in lemmas:
            question_type = "count" # e.g. 'How many X films are there?'

    return question_type


def get_entity_property_deps(parse, question_type):
    """
    Determine and clean entity and property from question type and parse
    :param parse: nlp parse of input question (spacy token object)
    :param question_type: question type abbreviation (str)
    :return: entity and propery (str)
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
                    pass

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
        entity_quotes = []
        entity_istitle = []
        for word in parse:
            if word.text == '"':
                entity_quotes.append((word.i, word.text))
            if word.text.istitle() and word.i != 0:
                entity_istitle.append((word.i, word.text))
        if len(entity_quotes) > 1:
            ent = parse[entity_quotes[0][0] + 1:entity_quotes[-1][0]].text.split(" ")
        elif entity_istitle:
            ent = parse[entity_istitle[0][0]:entity_istitle[-1][0] + 1].text.split(" ")
        else:
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
        entity_quotes = []
        entity_istitle = []
        for word in parse:
            if word.text == '"':
                entity_quotes.append((word.i, word.text))
            if word.text.istitle() and word.i != 0:
                entity_istitle.append((word.i, word.text))
        if len(entity_quotes) > 1:
            ent = parse[entity_quotes[0][0] + 1:entity_quotes[-1][0]].text.split(" ")
        elif entity_istitle:
            ent = parse[entity_istitle[0][0]:entity_istitle[-1][0] + 1].text.split(" ")
        else:
            ent = sent.split(" ")[dep.index("ROOT") + 1:]
        if 'from' in lemmas:
            prop = {'P19': 'place of birth', 'P495': 'country of origin'}
        elif 'filmed' in sent:
            prop = {'P915': 'filming location'}
        elif 'born' in lemmas:
            prop = {'P19': 'place of birth'}

    elif question_type == "time":
        entity_quotes = []
        entity_istitle = []
        for word in parse:
            if word.text == '"':
                entity_quotes.append((word.i, word.text))
            if word.text.istitle() and word.i != 0:
                entity_istitle.append((word.i, word.text))
        if len(entity_quotes) > 1:
            ent = parse[entity_quotes[0][0] + 1:entity_quotes[-1][0]].text.split(" ")
        elif entity_istitle:
            ent = parse[entity_istitle[0][0]:entity_istitle[-1][0] + 1].text.split(" ")
        else:
            ent = sent.split(" ")[dep.index("ROOT") + 1:]
        if 'born' in sent or 'birthday' in sent:
            prop = {'P569': 'date of birth'}
        elif 'release' in lemmas or 'come out' in sent or 'premiere' in sent \
                or 'publish' in lemmas or 'publicise' in lemmas:
            prop = {'P577': 'publication date'}
        elif 'die' in sent or 'pass away' in sent:
            prop = {'P570': 'date of death'}
        # Filter property answers based on data type of answer using VALUES
        pass
    elif question_type == "what_A_is_X_Y":
        entity_quotes = []
        entity_istitle = []
        for word in parse:
            if word.text == '"':
                entity_quotes.append((word.i, word.text))
            if word.text.istitle() and word.i != 0:
                entity_istitle.append((word.i, word.text))
        if len(entity_quotes) > 1:
            ent = parse[entity_quotes[0][0] + 1:entity_quotes[-1][0]].text.split(" ")
        elif entity_istitle:
            ent = parse[entity_istitle[0][0]:entity_istitle[-1][0] + 1].text.split(" ")
        else:
            ent = sent.split(" ")[dep.index("ROOT") + 1:]
        if parse[-2:].text.split(" ") == ['influenced', 'by'] or 'earned' in sent:
            prop = parse[-2:].text.split(" ")
        elif "AUX" in pos:
            prop = parse[1:pos.index("AUX")].text.split(" ")
    elif question_type == "what_which_verb":
        # Find entity
        # Find property: probably second word (parse[1])
        prop = [lemmas[1]]
    elif question_type == "whatXisY":
        # Find entity
        # Find property: probably words between first word and POS:AUX
        prop = parse[1:pos.index("AUX")].text.split(" ")
    elif question_type == "about":
        entity_quotes = []
        entity_istitle = []
        for word in parse:
            if word.text == '"':
                entity_quotes.append((word.i, word.text))
            if word.text.istitle() and word.i != 0:
                entity_istitle.append((word.i, word.text))
        if len(entity_quotes) > 1:
            ent = parse[entity_quotes[0][0] + 1:entity_quotes[-1][0]].text.split(" ")
        elif entity_istitle:
            ent = parse[entity_istitle[0][0]:entity_istitle[-1][0] + 1].text.split(" ")
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
        prop = parse[-2:].text.split(" ")

    elif question_type == "count":
        pass
    elif question_type == "yes/no":
        main_verb_id = dep.index("ROOT")
        ent = lemmas[1:main_verb_id]
        prop_broad = lemmas[main_verb_id + 1:]
        prop = [w for w in prop_broad if pos[lemmas.index(w)] != "DET"]

    else:
        pass

    # Filter entity: starts with first capital letter and start is not an adjective (e.g. the Dutch movie ...)
    try:
        start = min([ent.index(word) for word in ent if word.istitle() and
                     pos[sent.split(" ").index(word)] != "ADJ"])
        ent = ent[start:]
    except ValueError:
        pass

    # Convert entity and property from list to string
    ent = " ".join(ent)
    if type(prop) == list:
        prop = " ".join(prop)
        ent, prop = retrieve_id_label(ent, prop)
    else:
        ent, prop_irrelevant = retrieve_id_label(ent, "")

    return ent, prop


def phrase(word):
    """
    Returns a list of the full phrase, derived from a word
    :param word: word object from nlp parse (spacy token object)
    :return: phrase (list)
    """

    return [child.text for child in word.subtree]


def retrieve_id_label(ent, prop):
    """
    Get entity and property dictionaries with ids and labels
    :param ent: entity (str)
    :param prop: property (str)
    :return: entity and property dictionaries with key: id and value: label
    """

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
