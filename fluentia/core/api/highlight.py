def check_text_highlight(text, highlight_char='*'):
    text = text.split()
    for word in text:
        if word.startswith(highlight_char) and word.endswith(highlight_char):
            return True
    return False
