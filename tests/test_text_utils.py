import pytest

from .. import text_utils


class TestRemoveFirstOccurrence:
    texts = [
        ('my shiny string', 'shiny', 'my  string'),
        ('my shiny string is shiny', 'shiny', 'my  string is shiny'),
        ('the a) is is a) a) shiny', 'a)', 'the  is is a) a) shiny'),
        ('Exercise 1.', 'Exercise', ' 1.'),
        ('Exercise 1.', '1.', 'Exercise '),
        ('String not found', 'NotThere', 'String not found')
    ]

    @pytest.mark.parametrize("text, txt_find, out_text", texts)
    def test_remove_first_occurrence(self, text, txt_find, out_text, caplog):
        out = text_utils.remove_first_occurrence(text, txt_find)
        if text == out:
            assert caplog.record_tuples == [
                ('root', 30, ': Could not replace NotThere')
            ], 'Expected a logging warning'
        assert out == out_text


class TestMatchFirstWords:
    # note: returns sum of edit distances + number of checked words
    match_list = ['correct answer', 'answer', 'expected response']
    match_tests = [
        ('correct answer: d', match_list, True, [':'], 0, 2),
        ('answer: d', match_list, True, [':'], 0, 1),
        # not removing the last char means that edit distance is 1
        ('answer: d', match_list, False, [':'], 1, 1),
        ('correct answer: d', match_list, False, [':'], 1, 2),
        ('ansewr: d', match_list, True, [':'], 1, 1),
        # last char doesn't match any in the list
        ('answer: d', match_list, True, ['/', '('], 99999, 0),
        ('exected reponse: d', match_list, True, [':'], 2, 2),
    ]

    @pytest.mark.parametrize(
        "words, word_list, remove_last_char, last_char_match_list, "
        "expected_dist, expected_n_words", match_tests
    )
    def test_match_first_words(
        self, words, word_list, remove_last_char, last_char_match_list,
        expected_dist, expected_n_words
    ):
        dist, n_words = text_utils.min_first_words_match_list(
            words.split(), word_list, remove_last_char=remove_last_char,
            last_char_match_list=last_char_match_list
        )
        assert dist == expected_dist, 'Unexpected edit distances'
        assert n_words == expected_n_words, 'Number of words is incorrect'


class TestMatchFirstWordsExceptions:
    def test_raise_exception_word_not_splitted(self):
        """ Since a string becomes a list of words, it's important
            that the function checks that a string is not the input
        """
        with pytest.raises(AssertionError) as info:
            dist, n_words = text_utils.min_first_words_match_list(
                "Unexpected string", ['dum1', 'dum2'], remove_last_char=False
            )

        assert 'Words in the sentence should be already splitted'\
            in str(info.value)

    def test_raise_exception_no_splitter_list(self):
        """ If user wants to remove last char, we need
            a list for that
        """
        with pytest.raises(AssertionError) as info:
            dist, n_words = text_utils.min_first_words_match_list(
                ["my", "words"], ['dum1', 'dum2'], remove_last_char=True,
                last_char_match_list=None
            )
        assert 'Need delimiters' in str(info.value)

    def test_raise_exception_splitter_is_string(self):
        """ If user wants to remove last char, we need
            a list for that
        """
        with pytest.raises(AssertionError) as info:
            dist, n_words = text_utils.min_first_words_match_list(
                ["my", "words"], ['dum1', 'dum2'], remove_last_char=True,
                last_char_match_list=')}>.'
            )
        assert 'Possible delimiters must be a list' in str(info.value)
