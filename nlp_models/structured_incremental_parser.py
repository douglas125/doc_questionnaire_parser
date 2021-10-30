import re

import numpy as np


class IncrementalParser:
    """ Incremental Parser

    Attempts to find logical places to split a list of strings
    into coherent subsections.

    Example:

    Document1

    Some text
    Question 1. This
    Question 2. That

    Document2

    More text
    1. Do this
    2. Do that
    """

    def __init__(
        self, look_ahead=2, look_behind=4,
        ignore_spaces=True, max_num_questions=800,
        same_char_list=[')', '-', '.', ']', '}']
    ):
        """ Initializes incremental parser

        Arguments:

        look_behind: max number of characters to try to match behind
        look_ahead: max number of characters to try to match ahead
        ignore_spaces: ignore spaces ` ` when tryng to match
        max_num_questions: (reasonable) value for maximum number of questions
            e.g. we don't expect a doc to contain 3400 questions
            helps with matching
        same_char_list: characters to consider the same
        """
        self.look_behind = look_behind
        self.look_ahead = look_ahead
        self.ignore_spaces = ignore_spaces
        self.max_num_questions = max_num_questions
        self.same_char_list = same_char_list

    def parse_text_lines_inc_numbers(self, lines, lines_without_html):
        """ Parses a list of strings into coherent split indexes
            using as logic splitter an incremental sequence of numbers

        Arguments:

        lines - list of strings to parse

        Returns:
            a list of indexes to split lines in a coherent way
            e.g. the first line of each exercise
        """
        assert type(lines) == list, 'Expected `lines` to be a list'
        assert len(lines) == len(lines_without_html),\
            'Expected `lines` and `lines_without_html` to have the same length'

        question_idxs = []
        rep_txts = []

        # identify first number and their positions
        number_infos = []
        for idx, line_no_html in enumerate(lines_without_html):
            cur_txt = line_no_html.strip().lower()
            if self.ignore_spaces:
                cur_txt = cur_txt.replace(' ', '')
            # same chars
            for c in self.same_char_list:
                cur_txt = cur_txt.replace(c, self.same_char_list[0])
            rep_txts.append(cur_txt)
            first_number_info = re.search('[0-9]+', cur_txt)
            if first_number_info is not None:
                cur_span = first_number_info.span()
                number_infos.append({
                    'line_number': idx,
                    'span': cur_span,
                    'value': int(first_number_info.group()),
                    # reverse the look_behind
                    'look_behind': cur_txt[:cur_span[0]][::-1],
                    'look_ahead': cur_txt[
                        cur_span[1]:cur_span[1] + self.look_ahead
                    ]
                })

        look_ahead_texts = [s['look_ahead'] for s in number_infos
                            if s is not None]
        ahead_cands = self._find_common_string_pattern(look_ahead_texts, self.look_ahead)
        look_behind_texts = [s['look_behind'] for s in number_infos
                             if s is not None]
        behind_cands = self._find_common_string_pattern(look_behind_texts, self.look_behind)

        ahead_cands = [x for x in ahead_cands if x[1] <= self.max_num_questions]
        behind_cands = [x for x in behind_cands if x[1] <= self.max_num_questions]
        # logging.debug(f'Behind string: {behind_cands}\nAhead: {ahead_cands}')

        # find matches
        behind_str = behind_cands[0][0][::-1]
        ahead_str = ahead_cands[0][0]
        for info in number_infos:
            idx = info['line_number']
            behind_txt = rep_txts[idx][info['span'][0] - len(behind_str):info['span'][0]]
            ahead_txt = rep_txts[idx][info['span'][1]:info['span'][1] + len(ahead_str)]
            if behind_str == '':
                # require ahead match + info['span'][0] == 0
                if info['span'][0] == 0 and ahead_txt == ahead_str:
                    question_idxs.append(idx)
            else:
                # require ahead and behind match
                if behind_txt == behind_str and ahead_txt == ahead_str:
                    question_idxs.append(idx)
        return question_idxs

    def _find_common_string_pattern(self, text_list, max_chars):
        """ Attempts to find a string pattern in a text list

        Returns: sorted list with decreasing number of matches
        """
        # first attempt: exact match
        # TODO: implement approximate search?

        candidates = {}
        for text in text_list:
            if len(text) > 0:
                for k in range(min(len(text), max_chars)):
                    cur_text = text[0:k + 1]
                    candidates[cur_text] = candidates.get(cur_text, 0) + 1
            else:
                candidates[''] = candidates.get('', 0) + 1
        cand_text, cand_score = zip(*candidates.items())
        sorted_idxs = np.argsort(-np.array(cand_score))

        cand_score = [cand_score[x] for x in sorted_idxs]
        cand_text = [cand_text[x] for x in sorted_idxs]
        ans = list(zip(cand_text, cand_score))
        # logging.debug(ans)
        return ans
