import requests
from translate_a_thing import translate_text, Translation
from os import environ
from os.path import join, dirname
from dotenv import load_dotenv


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
    english = input(f'Enter english translation or leave blank to keep suggestion [{translation.english}]: ')
    english = english.strip() or translation.english
    return Translation(english=english, original=translation.original, original_language=translation.original_language)


if __name__ == '__main__':
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)

    translation = prompt_for_card()
    print(f'{translation.original} -> {translation.english}')

    client_id = environ['NAVER_CLIENT_ID']
    client_secret = environ['NAVER_CLIENT_SECRET']

    response = tts(translation.original, client_id, client_secret)
    response.raise_for_status()
    with open('output.mp3', 'wb') as outfile:
        outfile.write(response.content)