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
                question_type = "passive"  # e.g. 'Which movies are directed by X?'
                break
            elif any(item in duration_keywords for item in lemmas):
                question_type = "duration"  # e.g. 'How long is X?'
            elif any(item in location_keywords for item in lemmas):
                question_type = "location" # e.g. 'Where was X filmed?'
            elif any(item in time_keywords for item in lemmas):
                question_type = "time" # e.g. 'When was X published?'
            elif parse[0].text == "What" or parse[0].text == "Which":
                if parse[1].pos_ == "NOUN":
                    if "VERB" in pos:
                        if "AUX" in pos and lemmas[pos.index("AUX")] == "be":
                            question_type = "what_A_is_X_Y" # e.g 'What book is X based on?'
                        elif "AUX" in pos and lemmas[pos.index("VERB")] == "earn":
                            question_type = "what_A_is_X_Y" # e.g. 'Which movies earned X an award?'
                        else:
                            question_type = "what_which_verb" # e.g. 'What awards did X receive?'
    for rel in dep:
        if 'pass' in rel:
            question_type = "passive"  # e.g. 'Which movies are directed by X?'
            break
        elif any(item in duration_keywords for item in lemmas):
            question_type = "duration"  # e.g. 'How long is X?'
        elif any(item in location_keywords for item in lemmas):
            question_type = "location" # e.g. 'Where was X filmed?'
        elif any(item in time_keywords for item in lemmas):
            question_type = "time" # e.g. 'When was X published?'
        elif parse[0].text == "What" or parse[0].text == "Which" or parse[0].text == "Who":
            if 'pobj' in rel:
                question_type = "XofY"  # e.g. 'Who is the director of X?'
            elif parse[1].pos_ == "NOUN":
                if "VERB" in pos:
                    if "AUX" in pos and lemmas[pos.index("AUX")] == "be":
                        question_type = "what_A_is_X_Y" # e.g 'What book is X based on?'
                    elif "AUX" in pos and lemmas[pos.index("VERB")] == "earn":
                        question_type = "what_A_is_X_Y" # e.g. 'Which movies earned X an award?'
                    else:
                        question_type = "whatXisY" # e.g. 'What genre is X?'
                elif 'about' in lemmas:
                    question_type = "about"
                else:
                    question_type = "what_is_Xs_Y" # e.g. 'What is X's hair color?'
            elif parse[0].text == "How":
                if parse[1].text == "tall":
                    question_type = "tall" # e.g 'How tall is X?'
                elif parse[1].text == "many":
                    question_type = "count" # e.g. 'How many X films are there?'
                else:
                    question_type = "cost" # e.g. 'How much did X cost to make?'
            else:
                question_type = "cost" # e.g. 'How much did X cost to make?'
        else:
            if 'dobj' in rel:
                question_type = "verb_prop"  # e.g. 'Who directed X?'

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
        # Find entity
        prop = {'P2048': 'height'}
    elif question_type == "count":
        pass
    elif question_type == "cost":
        prop = {'P2130': 'cost'}
        pass
    elif question_type == "yes/no":
        main_verb_id = dep.index("ROOT")
        ent = lemmas[1:main_verb_id]
        prop_broad = lemmas[main_verb_id+1:-1]
        prop = [w for w in prop_broad if pos[lemmas.index(w)] != "DET"]

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

    # Retrieve Wikidata answer
    try:
        for prop in json['search']:
            for ent in json_e['search']:  # double for loop: match prop and ent correctly
                prop_id = prop['id']
                ent_id = ent['id']

                # Build query
                if question_type != "passive":
                    query = "SELECT ?answerLabel WHERE {SERVICE wikibase:label \
                    { bd:serviceParam wikibase:language '[AUTO_LANGUAGE],en'. } wd:" + ent_id + " wdt:" + prop_id + " ?answer .}"
                else:
                    query = "SELECT ?answerLabel WHERE {SERVICE wikibase:label \
                    { bd:serviceParam wikibase:language '[AUTO_LANGUAGE],en'. } ?answer wdt:" + prop_id + " wd:" + ent_id + " .}"

                # Send query and print results
                results = requests.get(sparql_url, params={'query': query, 'format': 'json'}).json()
                if question_type == "yes/no":
                    if results:
                        print("yes")
                    else:
                        print("no")
                    return
                else:
                    for item in results['results']['bindings']:  # We show all items: sometimes one name can refer to multiple possible entities!
                        for var in item:
                            print("The answer to your question is:", item[var]['value'])

    except:
        pass  # Not found


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
        return 'P2142' # Overlap with question type tall!
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
    elif 'university' in q:
        return 'P69' # Educated at


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
            # q = "Your question here"  # If you want to test a particular q
            question_type = get_question_type(q)
            ent, prop = get_entity_property(nlp(q), question_type)
            print('Q:\t', q)
            print('QT:\t', question_type)
            print('E:\t', ent)
            print('R:\t', prop)
            # retrieve_answer(prop, ent, question_type)  # Not optimised yet
            sys.stderr.write("\r" + "Answered question " + str(i) + " of " + str(total))
            sys.stderr.flush()
            i += 1
            print()
            print()


if __name__ == "__main__":
    main()
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
