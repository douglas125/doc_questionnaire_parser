import re
import string
import logging

from bs4 import BeautifulSoup
from docx2python import docx2python

import text_utils


LOWERCASE_CHARS = string.ascii_lowercase

DEFAULTCONFIG = {
    # edit this to change the output tags
    'ans_strings': {
        'stem': 'stem',
        'type': 'type',
        'multiple_choice': 'choice',
        'free_answer': 'long',  # why???
        # missing: short, when the answer is a single word or few?? words
        'options': 'choices',
        'option_text': 'text',
        'comment': 'comment',
        'correct_answer': 'correct_answer',
        'hints': 'hints',
        'tags': 'tags'
    },
    'exercise_strings': [
        'exercício',
        'exercicio',
        'exercise',
        'ejercicio',
        # seems appropriate
        'questão',
        'pergunta'
    ],
    'exercise_dist_tol': 2,
    'exercise_delimiter_tokens': [
        '.', ',', '-', ')',  # in documentation
        # seems reasonable
        ':', '|', '/', '\\', ']', '}', '>',
    ],
    'tag_dist_tol': 2,
    'tag_delimiter_tokens': [
        ')', ':', '='  # in documentation
    ],
    'possible_tags': {
        'correct_answer': ['resposta', 'resposta esperada', 'gabarito'],
        'detailed_answer': [
            'gabarito comentado',
            'resposta detalhada'
        ],
        'hint': ['dica'],
        'category': ['tags'],
        'difficulty': ['dificuldade'],
        'source': ['fonte'],
    },
    'source_begin_delimiters': ['(', '['],
    'source_end_delimiters': [')', ']'],
    # what follows the letter?
    'multiple_choice_delimiters':
    [
        ')', ']', '-', ' -', '. '
    ]
}


class SimilarityParser:
    """ Implements a text parser that is tolerant
        to multiple mistakes
        This is a hand engineered parser
    """

    def __init__(self, config=None):
        if config is not None:
            self.config = config
        else:
            self.config = DEFAULTCONFIG
        self.ans = self.config['ans_strings']

    def parse_docx(self, file_name):
        """ Attempts to parse a DOCX file into questions

        Arguments:

        file_name: DOCX file to process
        """
        contents = docx2python(file_name, html=True)

        pattern = "\(\d+, \d+, \d+, \d+\) "  # noqa
        html_txt = contents.html_map
        html_txt = re.sub(pattern, '', html_txt)

        lines = self._html_to_lines(html_txt)
        return self._parse_questions(lines)

    def _parse_questions(self, lines):
        question_idxs = self._split_questions(lines)
        questions = []
        if len(question_idxs) > 0:
            # don't forget last question
            if question_idxs[-1] != len(lines) - 1:
                question_idxs.append(len(lines) - 1)

            for (n1, n2) in zip(question_idxs[0:-1], question_idxs[1:]):
                q = self._parse_question(lines[n1:n2])
                questions.append(q)

        return questions

    def _html_to_lines(self, html_text):
        """ Receives a html parsed from docx2python and returns relevant lines
            in an array
        """
        lines = []
        soup = BeautifulSoup(html_text, features="lxml")
        for tbl in soup.findAll('table'):
            n_rows = len(tbl.findAll(
                lambda tag: tag.name == 'tr' and tag.findParent('table') == tbl
            ))
            n_cols = len(tbl.findAll(
                lambda tag: tag.name == 'td' and tag.findParent('table') == tbl
            ))
            if n_rows == 1 and n_cols == 1:
                for txt in tbl.findAll('pre'):
                    lines.append(
                        str(txt).replace('<pre>', '').replace('</pre>', '')
                    )
            else:
                lines.append(str(tbl))
        return lines

    def _split_questions(self, text_lines):
        """ Receives a list of lines and identifies
            where to split into different questions
        """
        question_idxs = []

        # look for question splitters
        for idx, cur_line in enumerate(text_lines):
            soup = BeautifulSoup(cur_line, features="lxml")
            words = soup.text.split()
            if len(words) > 1:
                question_distance = text_utils.min_word_distance(
                    words[0], self.config['exercise_strings']
                )

                valid_question_delimiter = words[1][-1] in self.config['exercise_delimiter_tokens']  # noqa
                is_valid_number = words[1][:-1].isnumeric()

                if question_distance <= self.config['exercise_dist_tol'] and\
                        valid_question_delimiter and is_valid_number:
                    question_idxs.append(idx)
                    # get rid of the delimiter text
                    # this is robust to multiple spaces
                    cur_val = text_utils.remove_first_occurrence(
                        cur_line, words[0], '_split_questions'
                    )
                    cur_val = text_utils.remove_first_occurrence(
                        cur_val, words[1], '_split_questions'
                    )
                    text_lines[idx] = cur_val

        return question_idxs

    # parse question tags
    def _parse_question_tags(self, question_lines):
        """ Attempts to identify tags in a question
        """
        tags = {'lines': [], 'types': [], 'values': []}
        for idx, cur_line in enumerate(question_lines):
            soup = BeautifulSoup(cur_line, features="lxml")
            words = soup.text.strip().split()
            for t in self.config['possible_tags']:
                tag_dist, n_words = text_utils.min_first_words_match_list(
                    words, self.config['possible_tags'][t],
                    remove_last_char=True,
                    last_char_match_list=self.config['tag_delimiter_tokens']
                )
                if tag_dist < self.config['tag_dist_tol']:
                    tags['lines'].append(idx)
                    tags['types'].append(t)

                    search_string = ' '.join(words[:n_words])
                    cur_val = text_utils.remove_first_occurrence(
                        cur_line, search_string, '_parse_question_tags'
                    )
                    tags['values'].append(cur_val)

        return tags

    # question parsing section
    def _parse_question(self, question_lines):
        """ Given a set of question lines,
            tries to parse text, options, answers and optionals
        """
        q_tags = self._parse_question_tags(question_lines)

        # remove tag lines
        non_tag_lines = set(range(len(question_lines))) - set(q_tags['lines'])
        non_tag_lines = list(non_tag_lines)
        non_tag_lines.sort()
        non_tag_lines = [question_lines[x] for x in non_tag_lines]

        # pick up source after question
        # question delimiter is already gone at this point
        if len(question_lines[0].split()) > 0:
            soup = BeautifulSoup(question_lines[0], features="lxml")
            first_line_text = soup.text.strip()

            source_candidate = first_line_text.split()[0]
            if source_candidate[0] in self.config['source_begin_delimiters']\
                    and len(source_candidate) > 2 and\
                    source_candidate[-1] in self.config['source_end_delimiters']:  # noqa
                q_tags['lines'].append(0)
                q_tags['types'].append('source')
                q_tags['values'].append(source_candidate[1:-1])

                cur_val = text_utils.remove_first_occurrence(
                    question_lines[0], source_candidate, '_parse_question'
                )
                non_tag_lines[0] = cur_val

        # try to parse multiple choice
        mc_parsing = self._try_parse_multiple_choice(non_tag_lines, q_tags)

        ans = {
            'all_parsed_tags': {
                'types': q_tags['types'],
                'values': q_tags['values']
            }
        }

        if mc_parsing is not None:
            ans[self.ans['stem']] = mc_parsing['question_text']
            ans[self.ans['type']] = self.ans['multiple_choice']
            ans[self.ans['options']] = [
                {'text': x} for x in mc_parsing['options']
            ]
        else:
            ans[self.ans['type']] = self.ans['free_answer']
            ans[self.ans['stem']] = '<br>'.join(non_tag_lines)

        extra_info = self._extract_info_from_tags(q_tags)
        ans.update(extra_info)

        return ans

    def _extract_info_from_tags(self, tags):
        """ Extracts relevant information from obtained tags,
            such as correct alternative
        """

        # all hints
        ans = {self.ans['hints']: []}
        for t, val in zip(tags['types'], tags['values']):
            if t == 'hint':
                ans[self.ans['hints']].append(val)
            elif t == 'detailed_answer':
                ans[self.ans['comment']] = val
            elif t == 'category':
                ans[self.ans['tags']] = val
            elif t == 'correct_answer':
                # pick up the letter and make it become a number
                question_ans_soup = BeautifulSoup(val, features="lxml")
                candidate = question_ans_soup.text.strip().lower()[-1]
                candidate = LOWERCASE_CHARS.index(candidate)
                if candidate >= 0:
                    ans[self.ans['correct_answer']] = candidate
                else:
                    logging.warning('_extract_info_from_tags: Cannot '
                                    f'understand correct answer from {tags[t]}')

        return ans

    # multiple choice parsing
    # this is so common that it deserves a section of its own
    def _try_parse_multiple_choice(self, question_lines, tags):
        """ Try to parse a multiple choice question
        """
        choice_candidate_lines = []
        choice_chars = []
        for idx, line in enumerate(question_lines):
            soup = BeautifulSoup(line, features="lxml")
            line_text = soup.text.strip()
            for delimiter in self.config['multiple_choice_delimiters']:
                if line_text[1:1 + len(delimiter)] == delimiter:
                    # logging.debug(f'{line_text}, {delimiter}')
                    choice_candidate_lines.append(idx)
                    choice_chars.append(line_text[0].lower())

                    search_string = line_text[0:1 + len(delimiter)]
                    cur_val = text_utils.remove_first_occurrence(
                        line, search_string, '_try_parse_multiple_choice'
                    )
                    question_lines[idx] = cur_val

        if len(choice_chars) >= 3 and\
                len(LOWERCASE_CHARS) >= len(choice_chars) and\
                LOWERCASE_CHARS[:len(choice_chars)] == ''.join(choice_chars):
            # good chance we're multiple choice here
            q_text = '<br>'.join(question_lines[0:choice_candidate_lines[0]])
            q_options = []
            for start, end in zip(choice_candidate_lines[:-1],
                                  choice_candidate_lines[1:]):
                q_options.append('<br>'.join(question_lines[start:end]))
            q_options.append('<br>'.join(question_lines[end:]))

            ans = {
                'question_text': q_text,
                'options': q_options
            }

            return ans
