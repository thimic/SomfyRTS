#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os

from threading import Lock

from somfy_rts.constants import MODEL_PATH
from somfy_rts.config import Config
from somfy_rts.shutter import Shutter


LOGGER = logging.getLogger(__name__)


class Model(dict):

    def __init__(self):
        """
        Model class constructor.
        """
        super(Model, self).__init__()
        self._lock = Lock()
        self.clear()
        self.load()

    def clear(self):
        """
        Clears model.
        """
        super(Model, self).clear()
        self['shutters'] = {}

    def load(self):
        """
        Load serialised model.
        """
        self._lock.acquire()
        try:
            if not os.path.isfile(MODEL_PATH):
                LOGGER.warning(f'No model found on disk: {MODEL_PATH}')
                return
            self.clear()
            with open(MODEL_PATH, 'r') as stream:
                shutters = json.load(stream).get('shutters') or {}
            for shutter_name, raw_shutter in shutters.items():
                shutter = Shutter.from_dict(raw_shutter)
                shutter.model = self
                self['shutters'][shutter_name] = shutter
        finally:
            self._lock.release()

    def dump(self):
        """
        Write out serialised model.
        """
        self._lock.acquire()
        try:
            with open(MODEL_PATH, 'w') as stream:
                json.dump(self, stream, indent=2)
        finally:
            self._lock.release()

    def register_shutter(self, shutter):
        """
        Registers shutter in the model. Sets the model as parent and generates a
        unique shutter address.

        Args:
            shutter (Shutter): New shutter

        """
        shutter.model = self
        shutter.address = self.get_next_address()
        self['shutters'][shutter.name] = shutter
        self.dump()

    def remove_shutter(self, name):
        """
        Remove shutter with the given name from the model if it exists.

        Args:
            name (str): Shutter name

        Returns:
            bool: True if the shutter was found and removed, else False

        """
        if name in self['shutters']:
            self.pop(name)
            self.dump()
            return True
        return False

    def get_shutter(self, name):
        """
        Get existing shutter by name.

        Args:
            name (str): Unique shutter name

        Returns:
            Shutter: Shutter

        """
        return self['shutters'].get(name)

    def get_next_address(self):
        """
        Gets the next available shutter address.

        Returns:
            int: Next available address

        """
        existing_addresses = [s.address for s in self['shutters'].values()]
        address = Config.pigpio.rts_address
        while address in existing_addresses:
            address += 1
        return address


if __name__ == '__main__':
    m = Model()
    print(Config.pigpio.rts_address)
    print(m.get_next_address())
