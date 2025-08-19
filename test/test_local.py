#!/usr/bin/env -S uv run --python-preference system --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "ida-domain",
# ]
# ///

import ida_domain

ida = ida_domain

# access ida_domain api
print(f"ida domain v{ida.__version__}")

# open a sample database
import tempfile, shutil
with tempfile.TemporaryDirectory() as temp_dir:
    temp_binary = f"{temp_dir}/ls"
    shutil.copy("/bin/ls", temp_binary)
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
