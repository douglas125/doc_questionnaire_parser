def enem_lines_parser(lines, text_lines_no_html):
    """ Specific enem lines parser
        Receives lines corresponding to one ENEM question
        and removes ENEM-specific lines

        ENEM has a page end marker like:
        *SA0175AZ3*
        we can ignore that and everything that comes after

    Arguments:

    lines: original lines identified as belonging to a question
    text_lines_no_html: parsed lines without html
    """
    final_idx = len(lines)
    for idx, x in enumerate(text_lines_no_html):
        cur_line = x.strip().lower()
        if cur_line.startswith('*s') and cur_line.endswith('*'):
            final_idx = idx
            break

    return lines[0:final_idx], text_lines_no_html[0:final_idx]
