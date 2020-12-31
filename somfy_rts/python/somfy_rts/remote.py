#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import pigpio
import subprocess
import time

from threading import Lock
from somfy_rts.config import Config
from somfy_rts.constants import Buttons

LOGGER = logging.getLogger(__name__)


class Remote:
    """
    Remote object.
    """

    def __init__(self):
        """
        Remote class constructor.
        """
        self.lock = Lock()
        self.pi = None

        # Set 433.42 MHz emitter pin. If no pin is given, assume pin 4.
        if Config.pigpio.txgpio is not None:
            self.txgpio = Config.pigpio.txgpio
        else:
            self.txgpio = 4

        # Connect to Pi
        self.start_pigpio()

    def start_pigpio(self):
        """
        Start pigpio daemon if it not running and verify that we can connect to
        it.
        """

        # Check if pigpio is running
        status, process = subprocess.getstatusoutput('pidof pigpiod')

        # If status is 0, pigpio is running
        if status != 0:
            LOGGER.warning('pigpiod was not running')

            # Try to  start it
            subprocess.getstatusoutput('pigpiod')
            time.sleep(0.5)

            # Check it again
            status, process = subprocess.getstatusoutput('pidof pigpiod')

        if status == 0:
            LOGGER.warning(f'pigpiod is running, process ID is {process}')
            try:
                # Local GPIO only
                self.pi = pigpio.pi()
                if not self.pi.connected:
                    raise RuntimeError(
                        'Unable to connect to GPIO interface. Aborting.'
                    )
            except Exception:
                LOGGER.exception('problem instantiating pigpio: ')
                return False
            LOGGER.warning('pigpio is instantiated')
            return True
        LOGGER.error('unable to start pigpiod')
        return False

    def lower(self, shutter):
        """
        Lower shutter with the given ID.

        Args:
            shutter (Shutter): Shutter

        """
        self.send_command(shutter, Buttons.Down, Config.pigpio.send_repeat)

    def rise(self, shutter):
        """
        Rise shutter with the given ID.

        Args:
            shutter (Shutter): Shutter

        """
        self.send_command(shutter, Buttons.Up, Config.pigpio.send_repeat)

    def stop(self, shutter):
        """
        Stop shutter with the given ID.

        Args:
            shutter (Shutter): Shutter

        """
        self.send_command(shutter, Buttons.Stop, Config.pigpio.send_repeat)

    def program(self, shutter):
        """
        Program shutter with the given ID.

        Args:
            shutter (Shutter): Shutter

        """
        self.send_command(shutter, Buttons.Program, 1)

    def lower_partial(self, shutter, timer):
        """
        Lower shutter with the given ID for the given number of seconds.

        Args:
            shutter (Shutter): Shutter
            timer (float) Seconds to lower shutter

        """
        self.send_command(shutter, Buttons.Down, Config.pigpio.send_repeat)
        time.sleep(timer)
        self.send_command(shutter, Buttons.Stop, Config.pigpio.send_repeat)

    def rise_partial(self, shutter, timer):
        """
        Rise shutter with the given ID for the given number of seconds.

        Args:
            shutter (Shutter): Shutter
            timer (float) Seconds to rise shutter

        """
        self.send_command(shutter, Buttons.Up, Config.pigpio.send_repeat)
        time.sleep(timer)
        self.send_command(shutter, Buttons.Stop, Config.pigpio.send_repeat)

    def send_command(self, shutter, button, repetition):
        """
        Sending a frame.

        Sending more than two repetitions after the original frame means a
        button kept pressed and moves the blind in steps to adjust the tilt.

        Sending the original frame and three repetitions is the smallest
        adjustment, sending the original frame and more repetitions moves the
        blinds up/down for a longer time.

        To activate the program mode (to register or de-register additional
        remotes) of your Somfy blinds, long press the program button (at least
        thirteen times after the original frame to activate the registration.

        Args:
            shutter (Shutter): Shutter
            button (Buttons): Remote control button
            repetition (int): Number of repetitions

        """
        frame = bytearray(7)
        LOGGER.warning('send_command: Waiting for Lock')
        self.lock.acquire()
        try:
            LOGGER.warning('send_command: Lock acquired')
            checksum = 0

            self.pi.wave_add_new()
            self.pi.set_mode(self.txgpio, pigpio.OUTPUT)

            LOGGER.warning(f'Shutter:\t\t{shutter.address:x} ({shutter.name})')
            LOGGER.warning(f'Button:\t\t{button.value:x} ({button.name})')
            LOGGER.warning(f'Rolling code:\t\t{shutter.code}')
            LOGGER.warning('')

            # Encryption key. Doesn't matter much
            frame[0] = 0xA7

            # Which button did you press? The 4 LSB will be the checksum
            frame[1] = button.value << 4

            # Rolling code (big endian)
            frame[2] = shutter.code >> 8

            # Rolling code
            frame[3] = shutter.code & 0xFF

            # Shutter address
            frame[4] = shutter.address >> 16

            # Shutter address
            frame[5] = (shutter.address >> 8) & 0xFF

            # Shutter address
            frame[6] = shutter.address & 0xFF

            # Increment shutter code by one
            shutter.code += 1

            outstring = 'Frame:\t\t' + ' '.join([f'0x{o:x}' for o in frame])
            LOGGER.warning(outstring)

            for i in range(0, 7):
                checksum = checksum ^ frame[i] ^ (frame[i] >> 4)

            checksum &= 0b1111  # We keep the last 4 bits only

            frame[1] |= checksum

            outstring = 'With cks:\t\t'
            for octet in frame:
                outstring = outstring + '0x%0.2X' % octet + ' '
            LOGGER.warning(outstring)

            for i in range(1, 7):
                frame[i] ^= frame[i - 1]

            outstring = 'Obfuscated:\t\t'
            for octet in frame:
                outstring = outstring + '0x%0.2X' % octet + ' '
            LOGGER.warning(outstring)

            # This is where all the awesomeness is happening. We're telling the
            # daemon what to send
            wf = [
                pigpio.pulse(1 << self.txgpio, 0, 9415),  # wake up pulse
                pigpio.pulse(0, 1 << self.txgpio, 89565)  # silence
            ]

            # hardware synchronization
            for i in range(2):
                wf.append(pigpio.pulse(1 << self.txgpio, 0, 2560))
                wf.append(pigpio.pulse(0, 1 << self.txgpio, 2560))

            # software synchronization
            wf.append(pigpio.pulse(1 << self.txgpio, 0, 4550))
            wf.append(pigpio.pulse(0, 1 << self.txgpio, 640))

            # manchester enconding of payload data
            for i in range(0, 56):
                if (frame[int(i / 8)] >> (7 - (i % 8))) & 1:
                    wf.append(pigpio.pulse(0, 1 << self.txgpio, 640))
                    wf.append(pigpio.pulse(1 << self.txgpio, 0, 640))
                else:
                    wf.append(pigpio.pulse(1 << self.txgpio, 0, 640))
                    wf.append(pigpio.pulse(0, 1 << self.txgpio, 640))

            # interframe gap
            wf.append(pigpio.pulse(0, 1 << self.txgpio, 30415))

            # repeating frames
            for j in range(1, repetition):

                # hardware synchronization
                for i in range(7):
                    wf.append(pigpio.pulse(1 << self.txgpio, 0, 2560))
                    wf.append(pigpio.pulse(0, 1 << self.txgpio, 2560))

                # software synchronization
                wf.append(pigpio.pulse(1 << self.txgpio, 0, 4550))
                wf.append(pigpio.pulse(0, 1 << self.txgpio, 640))

                # manchester enconding of payload data
                for i in range(0, 56):
                    if (frame[int(i / 8)] >> (7 - (i % 8))) & 1:
                        wf.append(pigpio.pulse(0, 1 << self.txgpio, 640))
                        wf.append(pigpio.pulse(1 << self.txgpio, 0, 640))
                    else:
                        wf.append(pigpio.pulse(1 << self.txgpio, 0, 640))
                        wf.append(pigpio.pulse(0, 1 << self.txgpio, 640))

                # interframe gap
                wf.append(pigpio.pulse(0, 1 << self.txgpio, 30415))

            # Add waveform
            self.pi.wave_add_generic(wf)

            # Send waveform
            wid = self.pi.wave_create()
            self.pi.wave_send_once(wid)

            # Wait for waveform to finish sending
            while self.pi.wave_tx_busy():
                time.sleep(0.1)

            # Delete waveform
            self.pi.wave_delete(wid)

        except Exception:
            LOGGER.exception('Failed to create and send waveform: ')

        finally:
            self.pi.wave_clear()
            self.lock.release()
            LOGGER.warning('send_command: Lock released')
