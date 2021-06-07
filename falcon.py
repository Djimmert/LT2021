#!/usr/bin/python3
# Description ...
# Authors: Jasper Bos (s3794687); Djim C. Casander (s3162753); Esther Ploeger (s3798461)
# Date:    June 8th, 2021


import requests
import csv


def call_falcon(text):
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    url = 'https://labs.tib.eu/falcon/falcon2/api?mode=long'
    entities = []
    relations = []
    payload = '{"text":"' + text + '"}'
    r = requests.post(url, data=payload.encode('utf-8'), headers=headers)
    if r.status_code == 200:
        response = r.json()
        for result in response['entities_wikidata']:
            entities.append(result[0])
            entities.append(result[1])
        for result in response['relations_wikidata']:
            relations.append(result[0])
            relations.append(result[1])
    else:
        r = requests.post(url, data=payload.encode('utf-8'), headers=headers)
        if r.status_code == 200:
            response = r.json()
            for result in response['entities_wikidata']:
                entities.append(result[0])
                entities.append(result[1])
            for result in response['relations_wikidata']:
                relations.append(result[0])
                relations.append(result[1])

    return entities, relations


def main():

    with open('test_questions.csv', 'r', encoding="utf-16") as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            print(row[1])
            entities, relations = call_falcon(row[1])
            print("Entities:", entities)
            print("Properties:", relations)
            print()


if __name__ == "__main__":
    main()