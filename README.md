# Questionnaire Parser
Convert DOCX and PDF files to structured questionnaires

## Installation

Create a conda environment using `requirements.txt` and install
pip requirements using `pip-requirements.txt`

## Usage:

- Import the parser of your choice
- Extract questions from a file by providing its path

Example:

```
from similarity_parser import SimilarityParser
sp = SimilarityParser()
questions = sp.parse_docx(path_to_docx_file)
```

`questions` will contain a list of dictionaries that represent each question
detected in the DOCX file


## Visualization

- Create a folder with files to be parsed (e.g. `data`) - right now, the parser will look for .DOCX and .PDF
- Select a folder to place outputs
- Run `parse_doc.py` as follows:

```
usage: parse_doc.py [-h] [-i INPUT] [-o OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input folder containing DOCX files to parse
  -o OUTPUT, --output OUTPUT
                        Output folder that will contain the parsed HTML files
```

As an example, simply run `python parse_doc.py` to process the files provided in the
`data` folder. The sample output will be placed inside the folder `output`
