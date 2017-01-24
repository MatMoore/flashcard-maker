import readline
from ankidb import add_card
from translate_a_thing import translate_text, Translation
import requests
from os import environ
from dotenv import load_dotenv
from pathlib import Path


def tts(text, client_id, client_secret):
    url = "https://openapi.naver.com/v1/voice/tts.bin"
    params = {
        'speaker': 'jinho',
        'speed': 5,
        'text': text.encode('utf8')
    }
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }

    return requests.post(url, data=params, headers=headers)


def prompt_for_card():
    text = input('Enter text to translate: ')

    translation = translate_text(target='en', text=text)

    print(f'Suggested translation: {translation.english}')
    keep = input('Keep suggestion y/n? [n]: ')

    if keep.strip().lower() == 'y':
        english = translation.english
    else:
        english = input('Enter translation (leave blank to cancel): ').strip()

    if not english:
        return None

    return Translation(english=english, original=translation.original, original_language=translation.original_language)


if __name__ == '__main__':
    dotenv_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path)

    readline.parse_and_bind("")

    client_id = environ['NAVER_CLIENT_ID']
    client_secret = environ['NAVER_CLIENT_SECRET']

    while True:
        try:
            translation = prompt_for_card()
        except (EOFError, KeyboardInterrupt):
            print('')
            break

        if translation is None:
            continue

        print(f'{translation.original} -> {translation.english}')

        response = tts(translation.original, client_id, client_secret)
        response.raise_for_status()


        add_card(
            front=translation.original,
            back=translation.english,
            sound=response.content,
            tags=()
        )
