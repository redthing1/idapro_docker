#!/usr/bin/env -S uv run --python-preference system --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rpyc",
#     "import-proxy",
# ]
# ///

import rpyc

c = rpyc.connect("127.0.0.1", 18812)

# proxy ida_domain import
import importproxy

importproxy.register("ida", importproxy.object_resolver(c.root.ida))

import ida
from ida import Database


def remote_temp_copy():
    tempfile = c.root.import_module("tempfile")
    shutil = c.root.import_module("shutil")
    temp_dir = tempfile.mkdtemp()
    temp_binary = f"{temp_dir}/ls"
    shutil.copy("/bin/ls", temp_binary)
    return temp_binary


print(f"ida domain v{ida.__version__}")

# open a sample database
temp_binary = remote_temp_copy()
with Database.open(path=temp_binary, save_on_close=False) as db:
    print(f"✓ Opened: {temp_binary}")
    print(f"  Architecture: {db.architecture}")
    print(f"  Entry point: {hex(db.entries[0].address)}")
    print(f"  Address range: {hex(db.minimum_ea)}-{hex(db.maximum_ea)}")

    # just get first function and decompile it
    first_func = next(iter(db.functions))
    pseudocode = db.functions.get_pseudocode(first_func)
    print(f"\n{db.functions.get_name(first_func)} @ {hex(first_func.start_ea)}:")
    for line in pseudocode:
        print(line)

print("✓ Database closed")
