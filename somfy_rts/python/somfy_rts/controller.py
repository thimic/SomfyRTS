#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging

from paho.mqtt.client import Client

from somfy_rts.config import Config
from somfy_rts.model import Model
from somfy_rts.remote import Remote
from somfy_rts.shutter import Shutter


LOGGER = logging.getLogger(__name__)


def on_connect(client, userdata, flags, rc):
    """
    The callback for when the client receives a CONNACK response from the
    server.

    Args:
        client (Client): MQTT client
        userdata (dict): MQTT client user data
        flags (dict): MQTT response flags
        rc (int): Connection result

    """
    LOGGER.warning(f'Connected with result code {rc}')

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(Config.mqtt.command_topic)
    client.subscribe(Config.mqtt.program_topic)


def on_message(client, userdata, msg):
    """
    The callback for when a PUBLISH message is received from the server.

    Args:
        client (Client): MQTT client
        userdata (dict): MQTT client user data
        msg (MQTTMessage): MQTT message

    """
    payload = json.loads(msg.payload)
    shutter_name = payload['name']
    if msg.topic == Config.mqtt.command_topic:
        shutter = client.model.get_shutter(shutter_name)
        LOGGER.debug(f'Received command on {msg.topic!r}: {payload}')
        if payload['command'] == 'up':
            client.remote.rise(shutter)
        elif payload['command'] == 'down':
            client.remote.lower(shutter)
        elif payload['command'] == 'stop':
            client.remote.stop(shutter)
    elif msg.topic == Config.mqtt.program_topic:
        LOGGER.debug(f'Received program command on {msg.topic!r}: {payload}')
        shutter = Shutter(shutter_name)
        client.model.register_shutter(shutter)
        try:
            client.remote.program(shutter)
        except Exception:
            LOGGER.exception(f'Unable to program shutter {shutter_name!r}: ')
            client.model.remove_shutter(shutter_name)
            return


class SomfyRTS(Client):

    def __init__(self):
        super().__init__()
        self.model = Model()
        LOGGER.warning(self.model)
        self.remote = Remote()

        self.username_pw_set(
            username=Config.mqtt.username,
            password=Config.mqtt.password
        )

        self.on_connect = on_connect
        self.on_message = on_message

    def start(self):
        self.connect(
            host=Config.mqtt.url,
            port=Config.mqtt.port,
            keepalive=Config.mqtt.keepalive
        )
        self.loop_forever()


def main():
    try:
        somfy_rts = SomfyRTS()
        somfy_rts.start()
    except Exception:
        LOGGER.exception('Failed to launch Somfy RTS: ')


if __name__ == '__main__':
    LOGGER.warning('About to start Somfy RTS...')
    main()
