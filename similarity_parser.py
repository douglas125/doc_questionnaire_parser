import string

import text_utils


LOWERCASE_CHARS = string.ascii_lowercase

DEFAULTCONFIG = {
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
        'answer': ['resposta', 'resposta esperada', 'gabarito'],
        'detailed_answer': [
            'gabarito comentado',
            'resposta detalhada'
        ],
        'category': ['tags'],
        'difficulty': ['dificuldade'],
        'hint': ['dica'],
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

    def parse_questions(self, text):
        lines = self._text_to_lines(text)
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

    def _text_to_lines(self, text):
        lines = text.splitlines()
        return lines  # [x for x in lines if len(x) > 0]

    def _split_questions(self, text_lines):
        """ Receives a list of lines and identifies
            where to split into different questions
        """
        question_idxs = []

        # look for question splitters
        for idx, cur_line in enumerate(text_lines):
            words = cur_line.split()
            if len(words) > 1:
                question_distance = text_utils.min_word_distance(
                    words[0], self.config['exercise_strings']
                )

                valid_question_delimiter = words[1][-1] in self.config['exercise_delimiter_tokens']  # noqa
                is_valid_number = words[1][:-1].isnumeric()

                if question_distance <= self.config['exercise_dist_tol'] and\
                        valid_question_delimiter and is_valid_number:
                    question_idxs.append(idx)

        return question_idxs

    # parse question tags
    def _parse_question_tags(self, question_lines):
        """ Attempts to identify tags in a question
        """
        tags = {'lines': [], 'types': [], 'values': []}
        for idx, cur_line in enumerate(question_lines):
            words = cur_line.split()
            for t in self.config['possible_tags']:
                tag_dist, n_words = text_utils.min_first_words_match_list(
                    words, self.config['possible_tags'][t],
                    remove_last_char=True,
                    last_char_match_list=self.config['tag_delimiter_tokens']
                )
                if tag_dist < self.config['tag_dist_tol']:
                    tags['lines'].append(idx)
                    tags['types'].append(t)
                    tags['values'].append(' '.join(words[n_words:]))

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
        if len(question_lines[0].split()) > 2:
            source_candidate = question_lines[0].split()[2]
            if source_candidate[0] in self.config['source_begin_delimiters'] and\
                    len(source_candidate) > 2 and\
                    source_candidate[-1] in self.config['source_end_delimiters']:
                q_tags['lines'].append(0)
                q_tags['types'].append('source')
                q_tags['values'].append(source_candidate[1:-1])
                non_tag_lines[0] = question_lines[0].replace(source_candidate,
                                                             '')

        # try to parse multiple choice
        mc_parsing = self._try_parse_multiple_choice(non_tag_lines, q_tags)

        ans = {
            'tags': {
                'types': q_tags['types'],
                'values': q_tags['values']
            }
        }

        if mc_parsing is not None:
            ans['question'] = mc_parsing
        else:
            ans['question'] = {'question_text', '\n'.join(non_tag_lines)}

        return ans

    # multiple choice parsing
    # this is so common that it deserves a section of its own
    def _try_parse_multiple_choice(self, question_lines, tags):
        """ Try to parse a multiple choice question
        """
        choice_candidate_lines = []
        choice_chars = []
        for idx, line in enumerate(question_lines):
            for delimiter in self.config['multiple_choice_delimiters']:
                if line.strip()[1:1 + len(delimiter)] == delimiter:
                    choice_candidate_lines.append(idx)
                    choice_chars.append(line[0].lower())
                    question_lines[idx] = line.strip()[1 + len(delimiter):].strip()

        if len(choice_chars) >= 3 and\
                len(LOWERCASE_CHARS) >= len(choice_chars) and\
                LOWERCASE_CHARS[:len(choice_chars)] == ''.join(choice_chars):
            # good chance we're multiple choice here
            q_text = '\n'.join(question_lines[0:choice_candidate_lines[0]])
            q_options = []
            for start, end in zip(choice_candidate_lines[:-1],
                                  choice_candidate_lines[1:]):
                q_options.append('\n'.join(question_lines[start:end]))
            q_options.append('\n'.join(question_lines[end:]))

            ans = {
                'question_text': q_text,
                'options': q_options
            }

            return ans
