# System.py
Three packages are required to run `system.py`.
## Installation
### Install [SpaCy](https://spacy.io/usage) and its language model
1. `pip3 install -U spacy`
2. `python3 -m spacy download en_core_web_md`

### Install [spacy-entity-linker 1.0.0](https://pypi.org/project/spacy-entity-linker/)
1. `pip3 install spacy-entity-linker`
2. `python3 -m spacy_entity_linker "download_knowledge_base"`

## Run system
`python3 system.py <input_file> <output_file>`
