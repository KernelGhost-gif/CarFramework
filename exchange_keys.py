#!/usr/bin/env python3
"""Exchange CarFramework public keys over UDP using a one-time pairing code."""
import argparse
import base64
import getpass
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import socket
import sys
import time

from cryptography.hazmat.primitives.asymmetric import mldsa

VERSION = 1


def encode(message, code=None):
    payload = dict(message)
    if code is not None:
        body = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
        payload['mac'] = hmac.new(code, b'carframework-key-exchange-v1\0' + body, hashlib.sha256).hexdigest()
    return json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()


def decode(data, code=None):
    try:
        message = json.loads(data)
        if not isinstance(message, dict) or message.get('v') != VERSION:
            return None
        if code is not None:
            tag = message.pop('mac', None)
            expected = json.loads(encode(message, code))['mac']
            if not isinstance(tag, str) or not hmac.compare_digest(tag, expected):
                return None
        return message
    except (ValueError, TypeError, UnicodeDecodeError):
        return None


def read_public(path):
    data = path.read_bytes()
    mldsa.MLDSA44PublicKey.from_public_bytes(data)
    return data


def save_public(path, data):
    mldsa.MLDSA44PublicKey.from_public_bytes(data)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if path.read_bytes() == data:
            print(f'Already present and matches: {path}', flush=True)
            return
        raise ValueError(f'{path} already exists with a different key; it was not overwritten')
    try:
        with os.fdopen(fd, 'wb') as file:
            file.write(data)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    print(f'Saved public key: {path}', flush=True)


def send(sock, address, kind, session, challenge=None, key=None, code=None):
    message = {'v': VERSION, 'type': kind, 'session': session}
    if challenge is not None:
        message['challenge'] = challenge
    if key is not None:
        message['key'] = base64.b64encode(key).decode('ascii')
    sock.sendto(encode(message, code), address)


def extract_key(message):
    try:
        key = base64.b64decode(message['key'], validate=True)
        mldsa.MLDSA44PublicKey.from_public_bytes(key)
        return key
    except (KeyError, ValueError, TypeError):
        return None


def exchange_sender(sock, peer, public_key, destination, code, deadline):
    session = secrets.token_hex(16)
    challenge = None
    while time.monotonic() < deadline:
        if challenge is None:
            send(sock, peer, 'hello', session)
        else:
            send(sock, peer, 'sender_key', session, challenge, public_key, code)
        try:
            data, address = sock.recvfrom(8192)
        except socket.timeout:
            continue
        if address != peer:
            continue
        message = decode(data, code)
        if not message or message.get('session') != session:
            continue
        if message.get('type') == 'challenge' and challenge is None:
            candidate = message.get('challenge')
            if isinstance(candidate, str) and len(candidate) == 32:
                challenge = candidate
        elif message.get('type') == 'receiver_key' and challenge is not None and message.get('challenge') == challenge:
            key = extract_key(message)
            if key is None:
                continue
            save_public(destination, key)
            for _ in range(3):
                send(sock, peer, 'ack', session, challenge, code=code)
            print('Public-key exchange complete.', flush=True)
            return
    raise TimeoutError('No authenticated response. Check the pairing code, IP address, port, and firewall.')


def exchange_receiver(sock, public_key, destination, code, deadline):
    pending = {}
    print('Listening for the sender...', flush=True)
    while time.monotonic() < deadline:
        try:
            data, address = sock.recvfrom(8192)
        except socket.timeout:
            continue
        message = decode(data)
        if not message:
            continue
        kind, session = message.get('type'), message.get('session')
        if not isinstance(session, str) or len(session) != 32:
            continue
        if kind == 'hello':
            # A fresh challenge prevents replay of a captured authenticated key.
            if (address, session) not in pending:
                pending.clear()
                pending[(address, session)] = secrets.token_hex(16)
            send(sock, address, 'challenge', session, pending[(address, session)], code=code)
        elif kind == 'sender_key' and (address, session) in pending:
            verified = decode(data, code)
            challenge = pending[(address, session)]
            if not verified or verified.get('challenge') != challenge:
                continue
            key = extract_key(verified)
            if key is None:
                continue
            save_public(destination, key)
            # A repeated authenticated request gets the same response if a datagram was lost.
            send(sock, address, 'receiver_key', session, challenge, public_key, code)
        elif kind == 'ack' and (address, session) in pending:
            verified = decode(data, code)
            if verified and verified.get('challenge') == pending[(address, session)]:
                print('Public-key exchange complete.', flush=True)
                return
    raise TimeoutError('Exchange timed out. Check the pairing code and network connection; rerun both devices if needed.')


def main():
    parser = argparse.ArgumentParser(description='Exchange sender and receiver public keys over UDP.')
    parser.add_argument('role', choices=('sender', 'receiver'))
    parser.add_argument('--peer', help='Receiver IP address or hostname (required for sender)')
    parser.add_argument('--port', type=int, default=5007, help='UDP port (default: 5007)')
    parser.add_argument('--timeout', type=int, default=120, help='Timeout in seconds (default: 120)')
    parser.add_argument('--key-dir', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    if args.role == 'sender' and not args.peer:
        parser.error('--peer is required for sender')
    if not 1 <= args.port <= 65535 or args.timeout <= 0:
        parser.error('port must be 1–65535 and timeout must be positive')
    try:
        key_dir = args.key_dir.expanduser().resolve()
        public = read_public(key_dir / f'{args.role}_mldsa_pk.bin')
        private = mldsa.MLDSA44PrivateKey.from_seed_bytes((key_dir / f'{args.role}_mldsa_sk.bin').read_bytes())
        if private.public_key().public_bytes_raw() != public:
            raise ValueError('The local public key does not match the local private key')
        raw_code = getpass.getpass('One-time pairing code (64 hexadecimal characters): ').strip()
        try:
            code = bytes.fromhex(raw_code)
        except ValueError:
            raise ValueError('Pairing code must be 64 hexadecimal characters') from None
        if len(raw_code) != 64 or len(code) != 32:
            raise ValueError('Pairing code must be 64 hexadecimal characters')
        peer_role = 'receiver' if args.role == 'sender' else 'sender'
        destination = key_dir / f'{peer_role}_mldsa_pk.bin'
        deadline = time.monotonic() + args.timeout
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(1)
            if args.role == 'receiver':
                sock.bind(('0.0.0.0', args.port))
                exchange_receiver(sock, public, destination, code, deadline)
            else:
                peer = (socket.gethostbyname(args.peer), args.port)
                exchange_sender(sock, peer, public, destination, code, deadline)
    except (OSError, ValueError, TimeoutError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
