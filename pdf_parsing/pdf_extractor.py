import io
import os
import logging

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


def _intersects(bb1, bb2):
    """ bbs in format (x1, y1, x2, y2)
    """

    if (bb1[0] == bb1[2] or bb1[1] == bb1[3]
            or bb2[0] == bb2[2] or bb2[1] == bb2[3]):
        # the line cannot have positive overlap
        return False

    # If one rectangle is on left side of other
    if(bb1[0] >= bb2[2] or bb2[0] >= bb1[2]):
        return False

    # If one rectangle is above other
    if(bb1[1] >= bb2[3] or bb1[3] >= bb2[1]):
        return False

    return True


def _reorder_lines_to_match_bb(text_bboxes, img_bboxes):
    """ Given line index of text_bboxes amd img_bboxes,
        figures if line indexes of img_bboxes need to be changed
        so that the figures fall into the correct place
        *---------*
        |         |
        |         |
        |         |  *----*
        |         |  |    |
        *---------*  *----*
        *---------*
        |         |  *--------*
        |         |  |        |
        |         |  |        |
        |         |  *--------*
        *---------* -> figure out where to place image
    """
    # we always need some slack for x coordinate
    x_slack = 1.1
    found_wrong_image_bbox = False
    for img_bb in img_bboxes:
        for idx in range(len(text_bboxes)):

            # we want to find a position that
            # text_box_before.y < text_box_after.y
            # intersection(text_box_after.bb, img_bb) = empty
            text_bb = text_bboxes[idx]
            if idx < len(text_bboxes) - 1:
                text_bb_next = text_bboxes[idx + 1]

            # text is the very first thing
            if idx == 0 and img_bb['bbox'][3] < text_bb['bbox'][1]\
                    and img_bb['bbox'][0] <= text_bb['bbox'][2] * x_slack:
                    # and img_bb['bbox'][0] >= text_bb['bbox'][0]:
                print(f'Image at top\n{text_bb["order"]}\n{img_bb["order"]}')
                break
            # image between texts
            elif img_bb['bbox'][1] > text_bb['bbox'][3]\
                    and img_bb['bbox'][0] <= text_bb['bbox'][2] * x_slack\
                    and img_bb['bbox'][3] < text_bb_next['bbox'][1]\
                    and img_bb['bbox'][0] <= text_bb_next['bbox'][2] * x_slack:
                    # and img_bb['bbox'][0] >= text_bb['bbox'][0]\
                    # and img_bb['bbox'][0] >= text_bb_next['bbox'][0]:
                print(f'Image between texts \n{text_bb["order"]}\n{text_bb_next["order"]}\n{img_bb["order"]}')
                break
            # image last thing of first column
            elif img_bb['bbox'][1] > text_bb['bbox'][3]\
                    and img_bb['bbox'][0] <= text_bb['bbox'][2] * x_slack\
                    and img_bb['bbox'][1] > text_bb_next['bbox'][1]\
                    and text_bb['bbox'][2] < text_bb_next['bbox'][0]:
                    # and img_bb['bbox'][0] >= text_bb['bbox'][0]\
                print(f'Image last thing first column \n{text_bb["order"]}\n{text_bb_next["order"]}\n{img_bb["order"]}')
                break
            # image first thing of second column
            elif img_bb['bbox'][1] < text_bb['bbox'][1]\
                    and img_bb['bbox'][3] < text_bb_next['bbox'][1]\
                    and img_bb['bbox'][0] <= text_bb_next['bbox'][2] * x_slack\
                    and text_bb['bbox'][2] < text_bb_next['bbox'][0]:
                    # and img_bb['bbox'][0] >= text_bb_next['bbox'][0]\
                print(f'Image first thing second colum \n{text_bb["order"]}\n{text_bb_next["order"]}\n{img_bb["order"]}')
                break
            # image is the very last thing
            elif idx == len(text_bboxes) - 1\
                    and img_bb['bbox'][1] > text_bb['bbox'][3]\
                    and img_bb['bbox'][0] <= text_bb['bbox'][2] * x_slack:
                    # and img_bb['bbox'][0] >= text_bb['bbox'][0]:
                print(f'Image very last\n{text_bb["order"]}\n{img_bb["order"]}')
                break


def read_pdf_lines(file, image_folder=None):
    """ Reads PDF lines from a file

    Arguments:

    file: file to read from
    """
    all_lines = []
    pdf_file = fitz.open(file)
    image_idx = 1
    for num_page, page in enumerate(pdf_file):
        print(f'Page {num_page} *********************')

        page_lines = []
        text = page.get_text('dict')

        # keep track of text and image bboxes
        # in order to reposition images correctly
        text_bboxes = []
        img_bboxes = []
        for order, b in enumerate(text['blocks']):
            lines = [x for x in b.get('lines', [])]
            image = b.get('image', None)
            lines = [' '.join([
                _build_html_from_span(z) for z in x['spans']
            ]) for x in lines]

            page_lines += lines
            if image is not None:
                img_name = f'{str(image_idx).zfill(8)}'
                page_lines.append(f'----media/{img_name}.{b["ext"]}----')
                img_bboxes.append({
                    'order': order,
                    'lines': [page_lines[-1]],
                    'bbox': b['bbox']
                })
                if image_folder is not None:
                    _save_png_from_b64(
                        os.path.join(image_folder, img_name),
                        b['ext'],
                        image
                    )
                image_idx += 1
            else:
                text_bboxes.append({
                    'order': order,
                    'lines': lines,
                    'bbox': b['bbox']
                })

        if len(img_bboxes) > 0:
            # if the image bboxes are not in the correct order,
            # we need to adjust page_lines so that the image
            # comes after the text it should
            _reorder_lines_to_match_bb(text_bboxes, img_bboxes)
            # print(len(text_bboxes), len(img_bboxes), len(page_lines))
        all_lines += page_lines

    return all_lines
