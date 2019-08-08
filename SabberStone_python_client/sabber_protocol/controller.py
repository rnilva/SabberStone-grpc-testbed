from struct import *
from sabber_protocol.entities import *


class Controller:
    def __init__(self, data_bytes):
        fields = unpack('6i', data_bytes[0:24])
        (
            self.id,
            self.state,
            self.base_mana,
            self.remaining_mana,
            self.overload_locked,
            self.overload_owed,
        ) = fields

        offset = 24
        self.hero = Hero(data_bytes[offset:offset+Hero.size])
        offset += Hero.size
        self.hand_zone = HandZone(data_bytes[offset:])
        offset += self.hand_zone.size
        self.board_zone = BoardZone(data_bytes[offset:])
        offset += self.board_zone.size
        self.secret_zone = SecretZone(data_bytes[offset:])
        offset += self.secret_zone.size
        self.deck_zone = DeckZone(data_bytes[offset:])

        self.size = offset + self.deck_zone.size