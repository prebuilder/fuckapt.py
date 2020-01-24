__all__ = ("install", "remove", "purge")
import typing

import sh

aptGet = sh.Command("apt-get")


def install(*pkgs: typing.Iterable[str]):
	aptGet.install(["-y"] + pkgs)


def remove(*pkgs: typing.Iterable[str]):
	aptGet.remove(["-y"] + pkgs)


def purge():
	aptGet.autoremove("--purge")
