#!/usr/bin/env -S uv run --python-preference system --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rpyc",
# ]
# ///

import rpyc

c = rpyc.connect("127.0.0.1", 18812)


def remote_temp_copy():
    tempfile = c.root.import_module("tempfile")
    shutil = c.root.import_module("shutil")
    temp_dir = tempfile.mkdtemp()
    temp_binary = f"{temp_dir}/ls"
    shutil.copy("/bin/ls", temp_binary)
    return temp_binary


ida = c.root.ida
print(f"ida domain v{ida.__version__}")

# open a sample database
temp_binary = remote_temp_copy()
with ida.Database.open(path=temp_binary, save_on_close=False) as db:
    print(f"✓ Opened: {temp_binary}")
    print(f"  Architecture: {db.architecture}")
    print(f"  Entry point: {hex(db.entries[0].address)}")
    print(f"  Address range: {hex(db.minimum_ea)}-{hex(db.maximum_ea)}")
    func_count = len(list(db.functions))
    print(f"  Functions: {func_count}")
    string_count = len(list(db.strings))
    print(f"  Strings: {string_count}")
print("✓ Database closed")
