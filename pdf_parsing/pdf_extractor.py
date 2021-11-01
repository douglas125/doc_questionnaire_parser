import io
import os

import fitz
from PIL import Image


def _save_png_from_b64(file_name, extension, img_data):
    # im = Image.open(io.BytesIO(base64.b64decode(img_data)))
    im = Image.open(io.BytesIO(img_data))
    im.save(file_name + f'.{extension}', extension)


def _build_html_from_span(span, dot_single_char=True):
    """ Builds HTML from span
    dot_single_char = True means that any 2-length string ending with
        space will have the space replaced by a dot.
        This simplifies downstream parsing but may be a TODO
    """
    cur_text = span['text']
    if dot_single_char and len(cur_text) == 2 and cur_text.endswith(' '):
        cur_text = cur_text.replace(' ', ')')

    if 'bold' in span["font"].lower():
        cur_text = f'<b>{cur_text}</b>'
    ans = [
        f'<p style="font-family:\'{span["font"]}\';',
        f' font-size:{span["size"]}pt">',
        cur_text,
        '</p>'
    ]
    # TODO: color
    # print(span['color'])

    return ''.join(ans)


def read_pdf_lines(file, image_folder=None):
    """ Reads PDF lines from a file

    Arguments:

    file: file to read from
    """
    all_lines = []
    pdf_file = fitz.open(file)
    image_idx = 1
    for page in pdf_file:
        # text = page.get_text('html')
        text = page.get_text('dict')
        for b in text['blocks']:
            lines = [x for x in b.get('lines', [])]
            image = b.get('image', None)
            lines = [' '.join([
                _build_html_from_span(z) for z in x['spans']
            ]) for x in lines]

            all_lines += lines
            if image is not None:
                img_name = f'{str(image_idx).zfill(8)}'
                all_lines.append(f'----media/{img_name}.{b["ext"]}----')
                if image_folder is not None:
                    _save_png_from_b64(
                        os.path.join(image_folder, img_name),
                        b['ext'],
                        image
                    )
                image_idx += 1

    return all_lines
