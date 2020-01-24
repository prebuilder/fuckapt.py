__all__ = ("install",)

import typing
from pathlib import Path

import sh

dpkg = sh.Command("dpkg")


def install(*paths: typing.Iterable[Path]):
	dpkg(["-i"] + paths)
