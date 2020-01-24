__all__ = ("install",)

import typing
import sh
from pathlib import Path

dpkg = sh.Command("dpkg")

def install(*paths: typing.Iterable[Path]):
	dpkg(["-i"] + paths)
