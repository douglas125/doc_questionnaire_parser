import copy
import zipfile
import logging

import jellyfish
import numpy as np
from tqdm.auto import tqdm


def read_embeddings(embeddings_file, print_errors=False):
    emb_dict = {}
    with zipfile.ZipFile(embeddings_file) as z:
        emb_file = z.namelist()
        assert len(emb_file) == 1, 'Embedding zip has more than 1 file'
        with z.open(emb_file[0]) as f:
            first_line = next(f)
            n_items = int(first_line.decode(encoding='UTF-8').split()[0])
            for line in tqdm(f, total=n_items):
                try:
                    items = line.decode(encoding='UTF-8').split()
                    if len(items) > 2:
                        emb_dict[items[0]] = [float(x) for x in items[1:]]
                except ValueError:
                    if print_errors:
                        print(f'Problem with {line}')
    return emb_dict


def word_distance(w1, w2):
    """ Computes word distance
    """
    return jellyfish.damerau_levenshtein_distance(w1.lower(), w2.lower())


def min_word_distance(word, word_list):
    """ Returns the smallest word distance from a list
    """
    distances = [word_distance(word, x) for x in word_list]
    return min(distances)


def min_first_words_match_list(
    words, word_list,
    remove_last_char=True,
    last_char_match_list=None
):
    """ Attempts to match the list of words with a word list
        For example: try to match `Correct answer` in word list
        with `corect answr: A` in words

    Arguments:

    words: list of words in the line. eg: ['Correct', 'answer:', 'B']
    word_list: match possibilities eg: ['correct answer', 'expected response']
    remove_last_char: if True, remove last char from last word to compare
        useful to enforce enders like `:`
    last_char_match_list: if remove_last_char=True, enforces
        last char to match one in the given list

    Returns:

    tuple (min_dist, n_compared_words) with minimum found
        distance and number of initial words needed to match
    """
    assert type(words) == list,\
        'Words in the sentence should be already splitted'
    if remove_last_char:
        assert last_char_match_list is not None, 'Need delimiters'
        assert type(last_char_match_list) == list,\
            'Possible delimiters must be a list'

    distances = []
    n_compared_words = []
    for ww in word_list:
        wsplit = ww.split()
        n_words = len(wsplit)
        if len(words) >= n_words:
            # check if last char matches
            if last_char_match_list is not None:
                last_char = words[n_words - 1][-1]
                last_char_match = last_char in last_char_match_list
            else:
                last_char_match = True

            if last_char_match:
                cur_dist = 0
                if remove_last_char:
                    cur_words = copy.deepcopy(words[0:n_words])
                    cur_words[-1] = cur_words[-1][:-1]
                else:
                    cur_words = words[0:n_words]

                for (query, truth) in zip(cur_words, wsplit):
                    # print(f'Comparing `{query}` with `{truth}`')
                    cur_dist += word_distance(query, truth)
                distances.append(cur_dist)
                n_compared_words.append(n_words)

    if len(distances) > 0:
        min_idx = np.argmin(distances)
        return distances[min_idx], n_compared_words[min_idx]
    else:
        # some big number
        return 99999, 0


def remove_first_occurrence(text, txt_find, caller_name=''):
    """ Removes the first occurrence in a text
        Throws a logging warning if it is not found
    """
    ans = text.replace(txt_find, '', 1)
    if ans == text:
        logging.warning(f'{caller_name}: Could not '
                        f'replace {txt_find}')
    return ans