import os
import re
import sys
import argparse

from tqdm import tqdm

from similarity_parser import SimilarityParser


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Parses PDF and DOCX documents into JSON format '
                    'renderable with HTML. In the case of PDF:\n'
                    '<file>.pdf - questions; <file>_gab.pdf - answers'
    )
    parser.add_argument(
        '-i',
        '--input',
        default='data',
        help='Input folder containing DOCX and PDF files to parse'
    )
    parser.add_argument(
        '-o',
        '--output',
        default='output',
        help='Output folder that will contain the parsed HTML files'
    )
    return parser.parse_args(sys.argv[1:])


def _adjust_img_url(x):
    ans = re.sub('----media/(.+?[^-])----', '<img src="images/\\1">', x)
    return ans


def replace_image_url(cur_dict):
    """ Replace all docx2python image strings
        with a proper path for visualization

    Arguments:

    cur_dict: dictionary whose values that contain
        images will get replaced by URLs
    """
    new_dict = {}
    for k in cur_dict:
        if type(cur_dict[k]) == dict:
            new_v = replace_image_url(cur_dict[k])
            new_dict[k] = new_v
        elif type(cur_dict[k]) == list:
            new_list = []
            for item in cur_dict[k]:
                if type(item) == dict:
                    new_item = replace_image_url(item)
                    new_list.append(new_item)
                elif type(item) == str:
                    new_item = _adjust_img_url(item)
                    new_list.append(new_item)

            new_dict[k] = new_list
        elif type(cur_dict[k]) == str:
            new_v = _adjust_img_url(cur_dict[k])
            new_dict[k] = new_v
        else:
            new_dict[k] = cur_dict[k]
    return new_dict


def question2html(orig_question, prev_html=None, next_html=None):
    """ Generates the HTML code to
        visualize question parsing
    """
    question = replace_image_url(orig_question)
    ans = ['<html><body>']
    # add links to prev and next
    if prev_html is not None:
        ans.append(f'<a href="{prev_html}">Previous</a>  ')
    if next_html is not None:
        ans.append(f'<a href="{next_html}">Next</a>')

    ans.append('<br><hr>')

    # read question text
    stem = question.pop('stem')
    ans.append(stem)
    if question['type'] == 'choice':
        options = question.pop('choices')
        correct_answer = question.get('correct_answer', -1)
        for idx, opt in enumerate(options):
            option_text = f'<br><br>Option {idx + 1}:<br>{opt["text"]}'
            if correct_answer == idx:
                option_text = '<p style="color:green; font-weight: bold">' +\
                              f'{option_text}</p>'
            ans.append(option_text)

    ans.append('<hr>Remaining info:<hr><br>')
    all_parsed_tags = question.pop('all_parsed_tags')
    for k in question:
        ans.append(f'<br><br>{k}:<br>{question[k]}')

    ans.append('<br><br><hr>All parsed tags:<hr>')
    for tag, val in zip(all_parsed_tags['types'], all_parsed_tags['values']):
        ans.append(f'<br><br>{tag}:<br>{val}')

    ans.append('</body></html>')
    return ''.join(ans)


def _gen_html_name(z):
    return str(z).zfill(8) + '.html'


def main(args):
    assert os.path.isdir(args.input),\
        f'Input folder not found: {args.input}'
    sp = SimilarityParser()
    doc_files = [x for x in os.listdir(args.input)
                 if x.lower().endswith('.docx')
                 or x.lower().endswith('.pdf')
                 and not x.lower().endswith('_gab.pdf')]
    os.makedirs(args.output, exist_ok=True)

    pbar = tqdm(doc_files)
    for document in pbar:
        # show user what document is being processed
        pbar.set_description(f'File: {document}')

        cur_out_folder = os.path.join(
            args.output, document.split('.')[0]
        )
        cur_out_imgs = os.path.join(cur_out_folder, 'images')
        os.makedirs(cur_out_imgs, exist_ok=True)
        if document.lower().endswith('.docx'):
            cur_parse = sp.parse_docx(
                os.path.join(args.input, document),
                image_folder=cur_out_imgs
            )
        elif document.lower().endswith('.pdf'):
            ans_file = None
            ans_candidate = os.path.join(
                args.input, document
            ).replace('.pdf', '_gab.pdf')

            if os.path.isfile(ans_candidate):
                ans_file = ans_candidate

            cur_parse = sp.parse_pdf(
                os.path.join(args.input, document),
                image_folder=cur_out_imgs,
                answers=ans_file
            )

        for idx, question in enumerate(cur_parse):
            html_name = _gen_html_name(idx + 1)
            prev_html = _gen_html_name(idx) if idx > 0 else None
            next_html = _gen_html_name(idx + 2)\
                if idx + 1 < len(cur_parse) else None

            with open(os.path.join(cur_out_folder, html_name),
                      'w', encoding='utf-8') as f:
                cur_txt = question2html(
                    question, prev_html=prev_html, next_html=next_html
                )
                f.write(cur_txt)


if __name__ == '__main__':  # pragma: no cover
    main(parse_arguments())
