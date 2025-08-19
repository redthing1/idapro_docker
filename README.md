
# idapro_docker

a docker image for ida pro 9.x+ that exposes a [rpyc](https://rpyc.readthedocs.io/en/latest/) service with the new [ida-domain](https://github.com/hexrayssa/ida-domain) api

## usage

### docker image

prepare the variables:
+ `IDA_DIR`: path to unpacked ida pro 9.x+ for linux
+ `IDA_LICENSE`: path to `.hexlic` license file

build the image:
```bash
docker build --platform linux/amd64 --build-arg IDA_DIR=ida-pro-9.1 --build-arg IDA_LICENSE=idapro.hexlic -t idapro:dev .
```

run the container:

```bash
docker run --rm -it -p 18812:18812 idapro:dev
```

connect from python:

```python
import rpyc
c = rpyc.connect("127.0.0.1", 18812)

# access ida_domain api
ida = c.root.ida
print(f"ida domain v{ida.__version__}")

# open a sample database
binary_path = "/bin/ls"
Database = ida.Database
with Database.open(path=binary_path, save_on_close=False) as db:
    print(f'✓ Opened: {binary_path}')
    print(f'  Architecture: {db.architecture}')
    print(f'  Entry point: {hex(db.entries[0].address)}')
    print(f'  Address range: {hex(db.minimum_ea)}-{hex(db.maximum_ea)}')
    func_count = len(list(db.functions))
    print(f'  Functions: {func_count}')
    string_count = len(list(db.strings))
    print(f'  Strings: {string_count}')
print('✓ Database closed')
```

### native

you can also use the server script natively on your own machine.

```sh
./ida_domain_server.py --ida-dir /path/to/ida
```
