"""
Manipulate cards in an Anki deck.

A collection database has several tables:

col stores configuration for the collection.  There is a row with a models
column, which in turn stores a JSON array of model configuration. A model
defines the format of a card, and the templates used to render it.

notes stores the information on a card. The flds column contains all the fields
belonging to a card, joined with an information separator value.

cards contains a row for each way you can be tested on a card, links the card
information to the deck, and stores the numbers that control when the card will
be shown.
"""
import json
import time
import random
import sqlite3
import string
from collections import namedtuple
from dotenv import load_dotenv
from hashlib import sha1
from os import environ
from pathlib import Path

MEDIA_PREFIX = "Generated_"

Card = namedtuple('Card', ('front', 'back', 'sound', 'tags'))


def add_card(**kwargs):
    card = Card(**kwargs)
    Collection.from_environ().add_card(card)


class StoredJson:
    column_name = NotImplemented

    def __init__(self, stored_dict):
        self._stored_dict = stored_dict

    @classmethod
    def load(cls, conn):
        stored_dict = json.loads(conn.execute(f'select {cls.column_name} from col').fetchone()[0])
        return Decks(stored_dict)
        
    def find_id_by_name(self, name):
        for item_id, item in self._stored_dict.items():
            if item['name'] == name:
                return item_id
        return None


class Decks(StoredJson):
    column_name = 'decks'


class Models(StoredJson):
    column_name = 'models'


class Collection:
    @staticmethod
    def from_environ():
        collection_db = Path(environ['ANKI_DATABASE']).expanduser()
        media_path = collection_db.parent / 'collection.media'
        conn = sqlite3.connect(str(collection_db))
        model_name = environ['MODEL_NAME']
        deck_name = environ['DECK_NAME']

        return Collection(
            conn=conn,
            media_path=media_path,
            deck_name=deck_name,
            model_name=model_name
        )

    def __init__(self, conn, media_path, deck_name, model_name):
        self.conn = conn
        self.media_path = media_path
        self.deck_name = deck_name
        self.model_name = model_name

    def _model_id(self):
        return Models.load(self.conn).find_id_by_name(self.model_name)

    def _deck_id(self):
        return Decks.load(self.conn).find_id_by_name(self.deck_name)

    def _next_noteid(self):
        '''
        Get the next id to use for the notes table, because it doesn't autoincrement
        '''
        return self.conn.execute('select max(id) from notes').fetchone()[0] + 1

    def _next_cardid(self):
        '''
        Get the next id to use for the cards table, because it doesn't autoincrement
        '''
        return self.conn.execute('select max(id) from cards').fetchone()[0] + 1

    def _add_card_row(self, noteid, deckid, required_fields=(0, 1)):
        """
        Add the required rows to the cards table for a new card

        required fields normally comes from model.req.
        For Cloze cards this works a bit differently.
        """
        for field_ord in required_fields:
            self.conn.execute(
                """
                insert into cards (
                    id, nid, did,
                    ord, mod, usn,
                    type, queue, due,
                    ivl, factor, reps,
                    lapses,  left, odue,
                    odid, flags,  data
                ) values (
                    ?,?,?,
                    ?,?,-1,
                    0,0, (select max(due) + 1 from cards), -- "show new cards in order added" mode
                    0,0,0,
                    0,0,0,
                    0,0,""
                )
                """,
                [
                    self._next_cardid(), noteid, deckid,
                    field_ord, int(time.time()),
                ]
            )

    def _add_media(self, filename, data):
        full_path = self.media_path / filename
        with open(full_path, 'wb') as outfile:
            outfile.write(data)

    # TODO: check for duplicates
    def add_card(self, card):
        model_id = self._model_id()
        deck_id = self._deck_id()

        if model_id is None:
            raise ValueError(f'Missing model: {model_name}')

        if deck_id is None:
            raise ValueError(f'Missing deck: {deck_name}')

        tags = ' '.join(card.tags)
        if tags:
            tags = f' {tags} '

        if card.sound:
            sound_filename = (MEDIA_PREFIX + card.front)
            self._add_media(sound_filename, card.sound)
            sound_field = f'[sound:{sound_filename}]'
        else:
            sound_field = ''

        # Encode the fields.
        # The order depends on how the fields are set up in the card model
        # (this is editable from "manage note types" in Anki)
        fields = '\x1f'.join((card.front, card.back, sound_field))

        # The field used for sorting in the card browser.
        # This is normally referenced by model.sfld.
        sort_field = card.front

        cursor = self.conn.cursor()
        cursor.execute(
            '''
            insert into notes(
                id, guid, mid,
                mod, usn, tags,
                flds, sfld, csum,
                flags, data
            ) values (
                ?, ?, ?,
                ?, -1, ?,
                ?, ?, ?,
                0, ''
            )
            ''',
            [
                self._next_noteid(), guid64(), model_id,
                int(time.time()), tags,
                fields, sort_field, field_checksum('flds[0]')
            ]
        )

        self._add_card_row(
            noteid=cursor.lastrowid,
            deckid=deck_id
        )

        self.conn.commit()


def guid64(extra="!#$%&()*+,-./:;<=>?@[]^_`{|}~"):
    "Return a base91-encoded 64bit random number."
    num = random.randint(0, 2**64-1)
    s = string; table = s.ascii_letters + s.digits + extra
    buf = ""
    while num:
        num, i = divmod(num, len(table))
        buf = table[i] + buf
    return buf


def field_checksum(data):
    # 32 bit unsigned number from first 8 digits of sha1 hash
    checksum = sha1(data.encode("utf-8")).hexdigest()
    return int(checksum[:8], 16)


if __name__ == '__main__':
    dotenv_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path)

    add_card(
        front='front3',
        back='back3',
        sound=None,
        tags=['test']
    )
