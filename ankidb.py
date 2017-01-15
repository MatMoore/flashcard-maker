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
from hashlib import sha1
from pathlib import Path

# Front/Back/Audio/Phonetics
MODEL_NAME = "Hangul Basic (and reversed card)"
DECK_NAME = "Korean Custom"

Card = namedtuple('Card', ('front', 'back', 'sound', 'tags'))


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
    def __init__(self, conn):
        self.conn = conn

    def _model_id(self, model_name):
        return Models.load(self.conn).find_id_by_name(model_name)

    def _deck_id(self, deck_name):
        return Decks.load(self.conn).find_id_by_name(deck_name)

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
                    0,0,0,
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

    # TODO: check for duplicates
    def add_card(self, card, model_name=MODEL_NAME, deck_name=DECK_NAME):
        model_id = self._model_id(model_name)
        deck_id = self._deck_id(deck_name)

        if model_id is None:
            raise ValueError(f'Missing model: {model_name}')

        if deck_id is None:
            raise ValueError(f'Missing deck: {deck_name}')

        tags = ' '.join(card.tags)
        if tags:
            tags = f' {tags} '

        fields = '\x1f'.join((card.front, card.back, card.sound or '', ''))

        # sfld in the model determines which field should be used
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
    conn = sqlite3.connect(str(Path('~/Documents/Anki/User 1/collection.anki2').expanduser()))
    card = Card(front='front', back='back', sound=None, tags=['test'])
    Collection(conn).add_card(card)
    conn.commit()
