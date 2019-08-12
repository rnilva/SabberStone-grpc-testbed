import socket
import platform
import numpy
import sys
import subprocess
import os
import signal
import time
from sabber_protocol.entities import *
from sabber_protocol.game import Game
from sabber_protocol.function import *
from sabber_protocol.option import *


SERVER_ADDRESS = '/tmp/CoreFxPipe_sabberstoneserver_'
MMF_NAME_POSTFIX = '_sabberstoneserver.mmf'
DEFAULT_SERVER_PATH = '../SabberStone_gRPC/'
TIMEOUT = 10


class SabberStoneServer:

    def __init__(self,
                 server_path=DEFAULT_SERVER_PATH,
                 id: str = "",
                 run_csharp_process=True):
        self.id = id
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        mmf_path = '../' + id + MMF_NAME_POSTFIX
        uds_path = SERVER_ADDRESS + id
        if run_csharp_process:
            csharp_server = subprocess.Popen(["dotnet", "run",
                                              "-p", server_path,
                                              "-v", "m",
                                              "-c", "Release",
                                              "mmf", id],
                                             stdout=subprocess.DEVNULL)
            self.csharp_server = csharp_server

            while True:
                now = time.time()
                timeout = now + TIMEOUT
                if (os.path.isfile(mmf_path)):
                    break
                if time.time() > timeout:
                    raise Exception('Can\'t connect to the server. (mmf timeout)')
            self.mmf_fd = open(mmf_path, 'r')
            self.mmf = numpy.memmap(self.mmf_fd, dtype='byte', mode='r',
                                shape=(10000))
            while True:
                try:
                    self.socket.connect(uds_path)
                    break
                except socket.error as e:
                    if time.time() > timeout:
                        raise Exception('''Can\'t connect to the server.
                    (uds timeout)''')
                    pass
        else:
            self.mmf_fd = open(mmf_path, 'r')
            self.mmf = numpy.memmap(self.mmf_fd, dtype='byte', mode='r',
                                shape=(10000))
            self.socket.connect(uds_path)

        print('Connected to SabberStoneServer')
        print('mmf length: {0}'.format(len(self.mmf)))

    def new_thread(self, thread_id: int):
        call_function_void_return(self.socket, 9)
        id = self.id + str(thread_id);
        print('Connecting to thread {0}......'.format(thread_id))
        return SabberStoneServer(id=id, run_csharp_process=False)

    def new_game(self, deckstr1, deckstr2):
        data_bytes = call_function_multiargs(self.socket, self.mmf, 4,
                                             deckstr1, deckstr2)
        return Game(data_bytes)

    def reset(self, game):
        data_bytes = call_function(self.socket, self.mmf, 5, game.id)
        return game.reset_with_bytes(data_bytes)

    def options(self, game):
        data_bytes = call_function(self.socket, self.mmf, 6, game.id)
        return get_options_list(data_bytes)

    def process(self, game, option):
        data_bytes = send_option(self.socket, self.mmf, game.id, option)
        return Game(data_bytes)

    def _test_get_one_playable(self):
        data_bytes = call_function(self.socket, self.mmf, 2, 0)
        return Playable(data_bytes)

    def _test_zone_with_playables(self):
        data_bytes = call_function(self.socket, self.mmf, 3, 0)
        return HandZone(data_bytes)

    def __del__(self):
        call_function_void_return(self.socket, 8)
        print('server {0} closed'.format(self.id))
