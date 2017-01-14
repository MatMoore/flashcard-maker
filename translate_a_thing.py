from google.cloud import translate
from collections import namedtuple

Translation = namedtuple('Translation', ('english', 'original_language', 'original'))


def translate_text(target, text):
    """Translates text into the target language.

    Target must be an ISO 639-1 language code.
    See https://g.co/cloud/translate/v2/translate-reference#supported_languages
    """
    translate_client = translate.Client()

    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = translate_client.translate(
        text,
        target_language=target)

    return Translation(
        english=result['translatedText'],
        original=result['input'],
        original_language=result['detectedSourceLanguage']
    )


if __name__ == '__main__':
    text = input(u'Enter text\n> ')
    print(translate_text(target='en', text=text))
