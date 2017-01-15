# Anki flashcard generator thingy

Generate Anki flashcards from the command line and add synthesised speech to them.

## Setup

### Dependencies

- Install python 3.6+
- (Optional) activate a [virtualenv](https://virtualenv.pypa.io/en/stable/)
- `pip install -r requirements.txt`

### Google translate API

Follow the [Google translate quick start guide](https://cloud.google.com/translate/docs/getting-started) to set up a service account.

Save the credential json file somewhere.

Run `dotenv set GOOGLE_APPLICATION_CREDENTIALS [path to json]`

### Naver API

Sign up for a developer account at https://developers.naver.com

Set up permissions for speech synthesis (음성합성)

You don't need any account stuff.

Note the client id and client secret and then run:

```
dotenv set NAVER_CLIENT_ID [client id]
dotenv set NAVER_CLIENT_SECRET [client secret]
```

### Anki

Install Anki and find the path to your collection (something like `~/Documents/Anki/User 1/collection.anki2`)

Run `dotenv set ANKI_DATABASE [collection path]`

Create a deck, and create a note type with an audio field. Then run:

```
dotenv set MODEL_NAME [model name]
dotenv set DECK_NAME [deck name]
```

## Usage

`python card_maker.py`
