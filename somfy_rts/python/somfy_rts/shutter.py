#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class Shutter(dict):

    def __init__(self, name, address=0, code=0, model=None):
        super(Shutter, self).__init__()
        self['name'] = name
        self['address'] = address
        self['code'] = code
        self._model = model

    @classmethod
    def from_dict(cls, dct):
        return Shutter(**dct)

    @property
    def name(self) -> str:
        return self.get('name')

    @property
    def address(self) -> int:
        return self.get('address')

    @address.setter
    def address(self, value):
        self['address'] = value

    @property
    def code(self) -> int:
        return self.get('code')

    @code.setter
    def code(self, value):
        self['code'] = value
        self.model.dump()

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        self._model = value


if __name__ == '__main__':
    s = Shutter('Bedroom', 2594340)
    print(str(s))
