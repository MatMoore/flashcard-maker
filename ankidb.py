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


class Collection:
    def __init__(self, conn):
        self.conn = conn

    def _model_id(self, model_name):
        return 123

    def _deck_id(self, deck_name):
        pass

    def _next_noteid(self):
        '''
        Get the next id to use for the notes table, because it doesn't autoincrement
        '''
        return self.conn.execute('select max(id) from notes').fetchone()[0] + 1

    # TODO: check for duplicates
    def add_card(self, card, model_name=MODEL_NAME, deck_name=DECK_NAME):
        model_id = self._model_id(model_name)

        tags = ' '.join(card.tags)
        if tags:
            tags = f' {tags} '

        fields = '\x1f'.join((card.front, card.back, card.sound or '', ''))

        # sfld in the model determines which field should be used
        sort_field = card.front

        self.conn.execute(
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
    conn.rollback()
