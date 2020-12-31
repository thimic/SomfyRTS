#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from somfy_rts.constants import CONFIG_PATH


class _Config(dict):

    def __init__(self, level='root', dictionary=None, parent=None):
        """
        Config constructor. Load from Addon config if dictionary parameter is
        None. Otherwise create sub-config section for parent config.

        Args:
            level (str): Config level. Top level is "root".
            dictionary (dict): Optional dictionary to populate config with
            parent (Config): Sub config's parent config

        """
        super().__init__()
        self._level = level
        self._parent = parent
        if not dictionary:
            self.load()
            return
        self.clear()
        self.update(dictionary)

    @property
    def parent(self):
        """
        Config's parent object. Root config returns None.

        Returns:
            Config: Parent config

        """
        return self._parent

    def load(self):
        """
        Load config from Addon json config.
        """
        with open(CONFIG_PATH, 'r') as stream:
            self.clear()
            self.update(json.load(stream))

    def __getattr__(self, item):
        """
        Allow config attributes to be accessed as properties.

        Args:
            item (str): Item name

        Returns:
            object: Item value

        """
        data = self.get(item)
        if isinstance(data, dict):
            return _Config(level=item, dictionary=data, parent=self)
        return data


Config = _Config()


if __name__ == '__main__':
    print(Config.pigpio.txgpio)
