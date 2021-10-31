# ensure that the output for some files is as expected
import os
import sys
import json
import inspect
import zipfile

import pytest

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from similarity_parser import SimilarityParser  # noqa


docx_files = [
    ('data/Questionario_exemplo_parser_no_images.docx',
     'tests/regression_data/Questionario_exemplo_parser_no_images.zip'),
    ('data/Open_questions.docx',
     'tests/regression_data/Open_questions.zip'),
]
pdf_files = [
    ('data/BAIXA_PPL_1_DIA_CADERNO_1_AZUL.pdf',
     'data/BAIXA_PPL_1_DIA_CADERNO_1_AZUL_gab.pdf',
     'tests/regression_data/enem2019.zip')
]


sp = SimilarityParser()


def load_json_from_zip(out_zip):
    with zipfile.ZipFile(out_zip, 'r') as zp:
        file = zp.namelist()[0]
        with zp.open(file) as f:
            data = f.read()
            expected_json = json.loads(data.decode("utf-8"))
    return expected_json


@pytest.mark.parametrize("in_file, out_zip", docx_files)
def test_docx_results(in_file, out_zip):
    computed_json = sp.parse_docx(in_file)
    # with open('docx_data.json', 'w') as f:
    #    json.dump(computed_json, f)
    expected_json = load_json_from_zip(out_zip)

    assert computed_json == expected_json,\
        f'Regression test failed for {in_file}'


@pytest.mark.parametrize("in_raw_file, in_raw_ans_file, out_zip", pdf_files)
def test_pdf_results(in_raw_file, in_raw_ans_file, out_zip):
    computed_json = sp.parse_pdf(in_raw_file, answers=in_raw_ans_file)
    # with open('pdf_data.json', 'w') as f:
    #    json.dump(computed_json, f)

    expected_json = load_json_from_zip(out_zip)
    assert computed_json == expected_json,\
        f'Regression test failed for {in_raw_file}'
