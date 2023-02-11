#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: fenc=utf-8 ts=4 sw=4 et

import sys
import kociemba
import argparse
import serial
import socket
from video import Webcam
import i18n
import os
from config import config
from constants import (
    ROOT_DIR,
    E_INCORRECTLY_SCANNED,
    E_ALREADY_SOLVED
)

# Set default locale.
locale = config.get_setting('locale')
if not locale:
    config.set_setting('locale', 'en')
    locale = config.get_setting('locale')

# Init i18n.
i18n.load_path.append(os.path.join(ROOT_DIR, 'translations'))
i18n.set('filename_format', '{locale}.{format}')
i18n.set('file_format', 'json')
i18n.set('locale', locale)
i18n.set('fallback', 'en')

class Qbr:

    def __init__(self, normalize, autoscan, remote):
        self.normalize = normalize
        self.autoscan = autoscan
        self.remote = remote

    def send_to_remote_serial(self, sol):
        buf = bytes(sol, 'utf-8')
        ard_client = serial.Serial(port='/dev/ttyUSB0', baudrate=115200, timeout=.1)
        ard_client.write(buf)
        ard_client.close()

    def send_to_remote_tcp(self, sol):
        buf = bytes(sol, 'utf-8')
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(("192.168.4.1", 50001))
            client.send(buf)
            client.close()
        except Exception as e:
            print("Exception: {0}".format(e))

    def send_to_remote_bluet(self, sol):
        buf = bytes(sol, 'utf-8')
        serverMACAddress = '00:1f:e1:dd:08:3d'
        port = 3
        try:
            blue_client = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            blue_client.connect((serverMACAddress, port))
            blue_client.send(buf)
            blue_client.close()
        except Exception as e:
            print("Exception: {0}".format(e))            

    def solve_cube(self, note):
        try:
            algorithm = kociemba.solve(note)
            length = len(algorithm.split(' '))
        except Exception as e:
            print("Exception: {0}".format(e))
            #self.print_E_and_exit(E_INCORRECTLY_SCANNED)

        print(i18n.t('startingPosition'))
        print(i18n.t('moves', moves=length))
        print(i18n.t('solution', algorithm=algorithm))
        
        if(self.remote):
            # send data to remote client
            self.send_to_remote_serial(algorithm)
            #self.send_to_remote_tcp(algorithm)
            #self.send_to_remote_bluet(algorithm)

        if self.normalize:
            for index, notation in enumerate(algorithm.split(' ')):
                text = i18n.t('solveManual.{}'.format(notation))
                print('{}. {}'.format(index + 1, text))                

    def run(self):
        """The main function that will run the Qbr program."""
        webcam = Webcam(self)

        state = webcam.run()

        # If we receive a number then it's an error code.
        # if isinstance(state, int) and state > 0:
        #     self.print_E_and_exit(state)

        # try:
        #     algorithm = kociemba.solve(state)
        #     length = len(algorithm.split(' '))
        # except Exception:
        #     self.print_E_and_exit(E_INCORRECTLY_SCANNED)

        # print(i18n.t('startingPosition'))
        # print(i18n.t('moves', moves=length))
        # print(i18n.t('solution', algorithm=algorithm))

        # if self.normalize:
        #     for index, notation in enumerate(algorithm.split(' ')):
        #         text = i18n.t('solveManual.{}'.format(notation))
        #         print('{}. {}'.format(index + 1, text))

        print("Exiting Qbr!")

    def print_E_and_exit(self, code):
        """Print an error message based on the code and exit the program."""
        if code == E_INCORRECTLY_SCANNED:
            print('\033[0;33m[{}] {}'.format(i18n.t('error'), i18n.t('haventScannedAllSides')))
            print('{}\033[0m'.format(i18n.t('pleaseTryAgain')))
        elif code == E_ALREADY_SOLVED:
            print('\033[0;33m[{}] {}'.format(i18n.t('error'), i18n.t('cubeAlreadySolved')))
        sys.exit(code)

if __name__ == '__main__':
    # Define the application arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-n',
        '--normalize',
        default=False,
        action='store_true',
        help='Shows the solution normalized. For example "R2" would be: \
              "Turn the right side 180 degrees".'
    )
    parser.add_argument(
        '-s',
        '--autoscan',
        default=False,
        action='store_true',
        help='scan automatically, with out pressing <SPACE>'
    )
    parser.add_argument(
        '-r',
        '--remote',
        default=False,
        action='store_true',
        help='send solution to remote client'
    )
    args = parser.parse_args()

    # Run Qbr with all arguments.
    Qbr(args.normalize, args.autoscan, args.remote).run()
