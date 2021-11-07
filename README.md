# Questionnaire Parser
Convert DOCX and PDF files to structured questionnaires

## Installation

Create a conda environment using `requirements.txt` and install
pip requirements using `pip-requirements.txt`

## Usage:

- Import the parser of your choice
- Extract questions from a file by providing its path
- Optionally, provide a folder that will be used to save images
- Optionally, provide an extra PDF with expected answers

Example:

```
from similarity_parser import SimilarityParser
sp = SimilarityParser()
questions = sp.parse_docx(path_to_docx_file, image_folder=folder_to_put_images)
```

`questions` will contain a list of dictionaries that represent each question
detected in the DOCX file

To parse a PDF file, use its name as argument and, optionally,
provide a file containing the corresponding answers.

```
from similarity_parser import SimilarityParser
sp = SimilarityParser()
questions = sp.parse_pdf(path_to_pdf_file, image_folder=folder_to_put_images, answers=path_to_pdf_answers)
```

### Provider specific parser

Sometimes, a PDF may contain provider specific parseable tags. To handle those, make sure
to add the provider name to the file name.

Supported provider-specific parsing at the moment:

- ENEM


## Visualization

- Create a folder with files to be parsed (e.g. `data`) - right now, the parser will look for .DOCX and .PDF
- Select a folder to place outputs
- Run `parse_doc.py` as follows:

```
usage: parse_doc.py [-h] [-i INPUT] [-o OUTPUT]

Parses PDF and DOCX documents into JSON format renderable with HTML.
In the case of PDF:

- <file>.pdf - questions;
- <file>_gab.pdf - answers

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input folder containing DOCX and PDF files to parse
  -o OUTPUT, --output OUTPUT
                        Output folder that will contain the parsed HTML files
```

As an example, simply run `python parse_doc.py` to process the files provided in the
`data` folder. The sample output will be placed inside the folder `output`
