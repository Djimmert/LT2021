from system_deps import *
from system_libs import *
import csv
import argparse

def merge_entities_properties(q, parse, question_type):
    deps_ent, deps_prop = get_entity_property_deps(parse, question_type)
    libs_ents, libs_props = get_entities_properties_libs(q)
    print("deps:\t", deps_ent, deps_prop)
    print("libs:\t", libs_ents, libs_props)

    return libs_ents | deps_ent, libs_props | deps_prop


def check_keywords(parse, q):
    q = q.lower()
    lemmas = [word.lemma_ for word in parse]

    if 'cult-like church' in q:
        return {'P140': 'religion'}
    elif 'named' in lemmas and 'after' in lemmas:
        return {'P138': 'named after'}
    elif 'film' in lemmas and 'location' in lemmas or 'where' in lemmas and 'film' in lemmas or \
            'film' in lemmas and 'country' in lemmas or 'film' in lemmas and 'city' in lemmas or \
            'film' in lemmas and 'place' in lemmas:
        return {'P915': 'filming location'}
    elif 'can' in lemmas and 'watch' in lemmas:
        return {'P750': 'distributed by'}
    elif 'company' in lemmas and 'direct' in lemmas or 'company' in lemmas and 'produce' in lemmas:
        return {'P272': 'production company'}
    elif 'how long' in q:
        return {'P2047': 'duration'}
    elif 'box office' in q:
        return {'P2142': 'box office'}
    elif 'when' in lemmas and 'publicise' in lemmas or 'when' in lemmas and 'release' in lemmas or \
            'when' in lemmas and 'come out' in q:
        return {'P577': 'publication date'}
    elif 'born' in lemmas and 'country' in lemmas or 'born' in lemmas and 'city' in lemmas or \
            'born' in lemmas and 'place' in lemmas:
        return {'P19': 'place of birth'}
    elif 'when' in lemmas and 'born' in lemmas:
        return {'P569': 'date of birth'}
    elif 'genre' in lemmas:
        return {'P136': 'genre'}
    elif 'main subject' in q:
        return {'P921': 'main subject'}
    elif 'original language' in q or 'language' in lemmas and 'spoken' in lemmas:
        return {'P364': 'original language of film or TV show'}
    elif 'cause' in lemmas and 'death' in lemmas or 'how' in lemmas and 'die' in lemmas:
        return {'P509': 'cause of death', 'P1196': 'manner of death'}
    elif 'follow' in lemmas:
        return {'P156': 'followed by'}
    elif 'catchphrase' in lemmas:
        return {'P6251': 'catchphrase'}
    elif 'how many children' in q:
        return {'P1971': 'number of children', 'P40': 'child'}
    elif 'country of citizenship' in q:
        return {'P27': 'country of citizenship'}
    elif 'country of origin' in q:
        return {'P495': 'country of origin'}



def retrieve_answer(q, question_type, ents, props):
    """
    """

    for entity_id in ents:
        for property_id in props:
            print(entity_id, property_id)
            # Build query
            if question_type != "passive":
                query = "SELECT ?answerLabel WHERE {SERVICE wikibase:label \
                { bd:serviceParam wikibase:language '[AUTO_LANGUAGE],en'. } wd:" + entity_id + " wdt:" + property_id + " ?answer .}"
            else:
                query = "SELECT ?answerLabel WHERE {SERVICE wikibase:label \
                { bd:serviceParam wikibase:language '[AUTO_LANGUAGE],en'. } ?answer wdt:" + property_id + " wd:" + entity_id + " .}"

            while True:
                try:
                    data = requests.get('https://query.wikidata.org/sparql',
                                    params={'query': query, 'format': 'json'}).json()
                    break

                except json.decoder.JSONDecodeError:  # Sometimes nothing is returned
                    continue  # Try again

            if data['results']['bindings']:
                results = []
                for item in data['results']['bindings']:
                    for var in item:
                        if item[var]['value']:
                            if 'coordinate' in q.lower():  # No language specified
                                if 'xml:lang' not in item[var]:
                                    results.append(item[var]['value'])
                                else:
                                    continue
                            elif 'year' in q.lower():  # No language specified and only return year
                                if 'xml:lang' not in item[var] and len(item[var]['value']) == 20:
                                    results.append(item[var]['value'][:4])
                            else:
                                results.append(item[var]['value'])

                if 'how many' not in q.lower() and 'how much' not in q.lower() and 'follower' not in q.lower() or 'cost' in q.lower():
                    if 'coordinate' in q.lower():  # No language specified
                        if 'xml:lang' not in item[var]:
                            return results
                        else:
                            continue
                    elif 'year' in q.lower():  # No language specified and only return year
                        if 'xml:lang' not in item[var] and len(item[var]['value']) == 20:
                            return results
                    return results
                else:
                    return len(results)


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
            print('Q:\t', q)
            parse = nlp(q)
            question_type = get_question_type(q)
            print('QT\t', question_type)
            ents, props = merge_entities_properties(q, parse, question_type)
            if check_keywords(parse, q):  # Overwrite
                print("[!] Property overwritten by keywords.")
                props = check_keywords(parse, q)
            print('E:\t', ents)
            print('R:\t', props)
            answer = retrieve_answer(q, question_type, ents, props)
            if question_type == "yes/no":
                if answer:
                    print("yes")
                else:
                    print("no")
            else:
                print(answer)
            print()

if __name__ == "__main__":
    main()
