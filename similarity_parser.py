import text_utils


DEFAULTCONFIG = {
    'exercise_strings': [
        'exercício',
        'exercicio',
        'exercise',
        'ejercicio',
        # seems good for later
        # 'questão', 'pergunta'
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
        'answer': ['resposta', 'resposta certa', 'resposta correta'],
        'detailed_answer': [
            'gabarito comentado',
            'resposta detalhada'
        ],
        'category': ['tags'],
        'difficulty': ['dificuldade'],
        'hint': ['dica'],
        'source': ['fonte'],
    }
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
                    words, self.config['possible_tags'][t]
                )
                if tag_dist < self.config['tag_dist_tol']:
                    tags['lines'].append(idx)
                    tags['types'].append(t)
                    tags['values'].append(words[n_words:])

        return tags

    # question parsing section
    def _parse_question(self, question_lines):
        """ Given a set of question lines,
            tries to parse text, options, answers and optionals
        """
        return self._parse_question_tags(question_lines)

    # multiple choice parsing
    # this is so common that it deserves a section of its own
    def _try_parse_multiple_choice(self, question_lines):
        """ Try to parse a multiple choice question
        """
        pass
