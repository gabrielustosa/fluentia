import string


def check_text_highlight(text, highlight_char='*'):
    punctuation_except_asterisk = ''.join([c for c in string.punctuation if c != '*'])
    translator = str.maketrans('', '', punctuation_except_asterisk)
    text = text.translate(translator).split()
    for word in text:
        if word.startswith(highlight_char) and word.endswith(highlight_char):
            return True
    return False
