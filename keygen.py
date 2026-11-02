#!/usr/bin/env python3
"""Create one device's ML-DSA identity for its first CarFramework setup."""

import argparse
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description="Create a sender or receiver ML-DSA key pair without overwriting existing keys.")
    parser.add_argument("role", choices=("sender", "receiver"), help="The role of this computer")
    parser.add_argument(
        "--output-dir", type=Path, default=Path(__file__).resolve().parent,
        help="Directory for the keys (defaults to the CarFramework folder)",
    )
    args = parser.parse_args()

    try:
        from cryptography.hazmat.primitives.asymmetric import mldsa
    except ImportError:
        parser.exit(1, "Error: install a version of cryptography with ML-DSA support in this Python environment.\n")

    output_dir = args.output_dir.expanduser().resolve()
    if not output_dir.is_dir():
        parser.exit(1, f"Error: output directory does not exist: {output_dir}\n")
    private_path = output_dir / f"{args.role}_mldsa_sk.bin"
    public_path = output_dir / f"{args.role}_mldsa_pk.bin"
    paths = (private_path, public_path)
    # Reserve both names before writing, and remove only files created by this run
    # if either reservation or write fails. Existing identity keys are never replaced.
    created = []
    handles = []
    try:
        private_key = mldsa.MLDSA44PrivateKey.generate()
        values = (private_key.private_bytes_raw(), private_key.public_key().public_bytes_raw())
        for path in paths:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            created.append(path)
            handles.append(os.fdopen(fd, "wb"))
        for handle, value in zip(handles, values):
            handle.write(value)
            handle.close()
    except Exception as exc:
        for handle in handles:
            handle.close()
        for path in created:
            path.unlink(missing_ok=True)
        parser.exit(1, f"Error: could not create key pair: {exc}\nExisting keys are never overwritten.\n")

    print(f"Created private key: {private_path}")
    print(f"Created public key:  {public_path}")
    print("Keep the private key on this device. Share only the public key with the other device.")


if __name__ == "__main__":
    main()
