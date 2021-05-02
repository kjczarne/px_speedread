from math import floor

f_words_per_line = lambda words_in_lines, num_lines: floor(words_in_lines/num_lines)
f_lines_per_page = lambda lines_in_pages, num_pages: floor(lines_in_pages/num_pages)


def avg_words_per_page(
    words_in_lines,
    lines_in_pages,
    num_lines=5,
    num_pages=5
):
    """
    Args:
        words_in_lines (int): total number of words counted on
                              `num_lines` lines
        lines_in_page (int): total number of lines counted on
                             `num_pages` pages
        num_lines (int): number of lines words were counted for
                         (default 5)
        num_pages (int): number of pages lines were counted for
                         (default 5)
    """
    wpl = f_words_per_line(words_in_lines, num_lines)
    lpp = f_lines_per_page(lines_in_pages, num_pages)
    return wpl * lpp


def words_per_minute(
    lines_read,
    words_per_line,
    minutes_spent=3
):
    """
    Args:
        lines_read (int): number of lines read in `minutes_spent` minutes
        words_per_line (int): words per line in the test book
        minutes_spent (int): how many minutes you've spent reading
    """
    return floor(lines_read * words_per_line / minutes_spent)


def time_per_line(
    desired_wpm, 
    words_per_line
):
    """
    Args:
        desired_wpm (int): the target words-per-minute value
                           you wish to achieve
        words_per_line (int): how many words per line your
                              test book contains on average
    Returns:
        seconds
    """
    # words_per_line * 1 min / 3 * desired_wpm
    minute_fraction = words_per_line/(3 * desired_wpm)
    return minute_fraction * 60
