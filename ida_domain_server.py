#!/usr/bin/env -S uv run --python-preference system --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "ida-domain",
#     "rpyc",
#     "typer>=0.15.0",
# ]
# ///

import os
import signal
import sys
from pathlib import Path

import rpyc
import typer
from rpyc.utils.server import ForkingServer

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

APP_NAME = "ida-domain-server"
app = typer.Typer(
    name=APP_NAME,
    help=f"{APP_NAME}: headless ida pro via remote procedure calls",
    no_args_is_help=True,
    context_settings=CONTEXT_SETTINGS,
    pretty_exceptions_short=True,
    pretty_exceptions_show_locals=False,
)


class IdaDomainService(rpyc.Service):
    """rpyc service exposing ida domain api"""

    def on_connect(self, conn):
        """called when client connects"""
        print(f"client connected: {conn}")

    def on_disconnect(self, conn):
        """called when client disconnects"""
        print(f"client disconnected: {conn}")

    @property
    def exposed_ida(self):
        """expose ida_domain module as 'ida'"""
        return ida_domain

    @property
    def exposed_ida_domain(self):
        """expose ida_domain module under full name"""
        return ida_domain

    def exposed_get_version(self):
        """get ida domain version info"""
        return (
            ida_domain.__version__ if hasattr(ida_domain, "__version__") else "unknown"
        )

    def exposed_eval(self, cmd):
        """evaluate python code"""
        return eval(cmd)

    def exposed_exec(self, cmd):
        """execute python code"""
        return exec(cmd)

    def exposed_import_module(self, mod):
        """import a module"""
        import importlib

        return importlib.import_module(mod)

    def exposed_add_to_syspath(self, path):
        """add path to sys.path"""
        return sys.path.append(path)

    def exposed_globals(self):
        """get global namespace"""
        return globals()

    def exposed_locals(self):
        """get local namespace"""
        return locals()


def signal_handler(signum, frame):
    """handle ctrl+c gracefully"""
    print("\nshutting down server...")
    sys.exit(0)


def validate_environment():
    """validate ida environment is properly configured"""
    # check if IDADIR is set
    idadir = os.environ.get("IDADIR")
    if not idadir:
        typer.echo(
            "error: IDADIR environment variable not set",
            err=True,
            color=typer.colors.RED,
        )
        typer.echo("please set IDADIR to your ida installation directory:", err=True)
        typer.echo(
            '  export IDADIR="/Applications/IDA Professional 9.1.app/Contents/MacOS"',
            err=True,
        )
        raise typer.Exit(1)

    # check if IDADIR path exists
    idadir_path = Path(idadir)
    if not idadir_path.exists():
        typer.echo(
            f"error: IDADIR path does not exist: {idadir}",
            err=True,
            color=typer.colors.RED,
        )
        raise typer.Exit(1)

    # check for ida binaries
    ida_binaries = ["ida64", "ida", "idat64", "idat"]
    found_binaries = []
    for binary in ida_binaries:
        binary_path = idadir_path / binary
        if binary_path.exists():
            found_binaries.append(binary)

    if not found_binaries:
        typer.echo(
            f"warning: no ida binaries found in {idadir}",
            err=True,
            color=typer.colors.YELLOW,
        )
        typer.echo("expected to find one of: ida64, ida, idat64, idat", err=True)
    else:
        typer.echo(f"found ida binaries: {', '.join(found_binaries)}")

    typer.echo(f"using IDADIR: {idadir}")

    # try to import ida_domain after validation
    try:
        global ida_domain
        import ida_domain

        typer.echo("ida_domain imported successfully")
    except ImportError as e:
        typer.echo(
            f"error: failed to import ida_domain: {e}", err=True, color=typer.colors.RED
        )
        raise typer.Exit(1)


@app.command()
def cli(
    host: str = typer.Option("127.0.0.1", "-h", "--host", help="host to bind to"),
    port: int = typer.Option(18812, "-p", "--port", help="port to bind to"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="verbose output"),
    ida_dir: str = typer.Option(
        None, "--ida-dir", help="ida installation directory (sets IDADIR)"
    ),
):
    """start ida domain rpyc server"""
    # set IDADIR if provided via command line
    if ida_dir:
        os.environ["IDADIR"] = ida_dir
        if verbose:
            typer.echo(f"setting IDADIR to: {ida_dir}")

    # validate environment first
    validate_environment()

    # setup signal handling for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"starting ida domain rpyc server on {host}:{port}")
    print("use ctrl+c to stop")

    if verbose:
        print()
        print("example client usage:")
        print("  import rpyc")
        print(f"  c = rpyc.connect('{host}', {port})")
        print("  ida = c.root.ida  # access ida_domain as 'ida'")
        print("  # or: ida_domain = c.root.ida_domain")
    print()

    # create and configure the server
    # forking server: each client gets their own ida process
    server = ForkingServer(
        IdaDomainService(),
        hostname=host,
        port=port,
        protocol_config={
            "allow_public_attrs": True,
            "allow_all_attrs": True,
            "allow_getattr": True,
            "allow_setattr": True,
            "allow_delattr": True,
            "allow_pickle": True,
            "sync_request_timeout": 3600,  # 1 hour
        },
    )

    try:
        server.start()
    except KeyboardInterrupt:
        print("\nserver stopped")
    except Exception as e:
        print(f"error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
