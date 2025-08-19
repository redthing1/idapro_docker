#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "rpyc",
# ]
# ///
"""
simple test client for ida domain rpyc server
"""

import rpyc


def test_connection():
    """test connection to ida domain server"""
    try:
        # connect to server
        c = rpyc.connect("127.0.0.1", 18812)
        print("connected to server successfully")

        # access ida domain via the 'ida' alias
        ida = c.root.ida
        print(f"ida_domain available: {ida}")

        # try to get version info
        version = c.root.get_version()
        print(f"ida domain version: {version}")

        # show available modules
        print("\navailable ida_domain modules:")
        for attr in sorted(dir(ida)):
            if not attr.startswith("_"):
                print(f"  {attr}")

        c.close()
        print("\nconnection closed")

    except Exception as e:
        print(f"error: {e}")


if __name__ == "__main__":
    test_connection()
