import pathlib
import subprocess
import sys


def main():
    if pathlib.Path(__file__).parent.stem == "sourcery_cli":
        print(
            "Package `sourcery-cli` is deprecated. Please use `pip install sourcery` instead\n",
            file=sys.stderr,
        )
    command = pathlib.Path(__file__).parent / "sourcery"
    return subprocess.call([str(command), *sys.argv[1:]], bufsize=0)
