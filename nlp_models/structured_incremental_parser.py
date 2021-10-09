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
        self, look_behind=8, look_ahead=3,
        same_char_list=[')', '-', '.', ']', '}']
    ):
        """ Initializes incremental parser

        Arguments:

        look_behind: max number of characters to try to match
            before incrementing numbers
        look_ahead: max number of characters to try to match ahead
        same_char_list: characters to consider the same
        """
        self.look_behind = look_behind
        self.look_ahead = look_ahead
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

        return question_idxs
