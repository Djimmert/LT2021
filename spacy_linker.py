#!/usr/bin/python3
# Description ...
# Authors: Jasper Bos (s3794687); Djim C. Casander (s3162753); Esther Ploeger (s3798461)
# Date:    June 8th, 2021

#pip3 install spacy-entity-linker
#python3 -m spacy_entity_linker "download_knowledge_base"

import spacy
import csv


def main():

    # initialize language model
    nlp = spacy.load("en_core_web_md")  # python3 -m spacy download en_core_web_md

    # add pipeline (declared through entry_points in setup.py)
    nlp.add_pipe("entityLinker", last=True)

    with open('test_questions.csv', 'r', encoding="utf-16") as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            doc = nlp(row[1])
            # returns all entities in the whole document
            all_linked_entities = doc._.linkedEntities
            # iterates over sentences and prints linked entities
            print(row[1])
            for sent in doc.sents:
                sent._.linkedEntities.pretty_print()


if __name__ == "__main__":
    main()