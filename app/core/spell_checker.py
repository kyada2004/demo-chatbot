from spellchecker import SpellChecker

spell = SpellChecker()

def correct_spelling(text):
    """
    Corrects the spelling of a given text.
    """
    words = text.split()
    corrected_words = []
    for word in words:
        # Get the one `most likely` answer
        corrected_word = spell.correction(word)
        if corrected_word is not None:
            corrected_words.append(corrected_word)
        else:
            corrected_words.append(word) # if no correction found, keep the original word
    return " ".join(corrected_words)