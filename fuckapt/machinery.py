__all__ = ("getAptInfo", "dpkgStatusFileLoc", "dpkgInfoFilesLoc", "defaultArch", "etcDir", "sourcesListFile", "sourcesPartsDir", "trustedKeyringPath", "trustedKeyringPartsPath", "aptLogDir", "aptStateDir", "aptPackageCacheBase", "aptBinaryPackageCache", "aptSourcePackageCache")

import re
import typing
from pathlib import Path

import sh
import sh.contrib
from debparse.deb_control import parse as debParse


def getAptVars(*vars):
	aptCfgCommand = sh.Command("apt-config")
	rawRes = aptCfgCommand.dump(*vars)
	res = {}
	for l in rawRes.splitlines():
		if l[-1] == "\n":
			l = l[:-1]
		if l[-1] == ";":
			l = l[:-1]
		k, v = l.split(" ", 1)
		if v[0] in {'"', "'"} and v[-1] == v[0]:
			v = v[1:-1]
		res[k] = v
	return res


architectureRemap = {
	("Linux", "x86_64"): "amd64",
	("Linux", "x86"): "i386",
	("Linux", "riscv64"): "riscv64",
	("GNU/Linux", "x86_64"): "amd64",
	("GNU/Linux", "x86"): "i386",
	("GNU/Linux", "riscv64"): "riscv64",
	("GNU/kFreeBSD", "x86_64"): "kfreebsd-amd64",
	("GNU/kFreeBSD", "x86"): "kfreebsd-i386",
}


fallbackEtcDir = Path("/etc/apt")
fallbackSourcesListFileName = "sources.list"
fallbackSourcesPartsDirName = fallbackSourcesListFileName + ".d"
fallbackTrustedKeyringFileName = "trusted.gpg"
fallbackTrustedKeyringPartsDirName = fallbackTrustedKeyringFileName + ".d"
fallbackAptLogDir = Path("/var/log/apt")
fallbackAptStateDir = Path("/var/lib/apt")

fallbackAptBinaryPackageCacheName = "pkgcache.bin"
fallbackAptSourcePackageCacheName = "srcpkgcache.bin"
fallbackAptPackageCacheBase = Path("/var/cache/apt")

aptKeyBinaryPath = Path("/usr/bin/apt-key")

# ToDo: https://github.com/Debian/apt/blob/master/apt-pkg/pkgcache.h


def _getDir(dic, paramName, fallback):
	res = dic.get(paramName, None)
	if res is not None:
		res = Path("/" + res)
	else:
		res = Path(fallback)
	assert res.is_dir()
	return res


def getHardcodedTrustedParts(aptKeyScript: Path = aptKeyBinaryPath):
	aptKeyScript = Path(aptKeyScript)
	for l in aptKeyScript.open("rt", encoding="utf-8"):
		m = trustedPartsRx.match(l)
		if m:
			return Path(m.group(1)).absolute()


def getAptInfo():
	try:
		aptVars = getAptVars("Dir::State::status", "APT::Architecture", "Dir::Etc", "Dir::Etc::sourcelist", "Dir::Etc::sourceparts", "Apt::GPGV::TrustedKeyring", "Dir::Etc::Trusted", "Dir::Etc::trustedparts", "Dir::Log", "Dir::State", "Dir::Cache", "Dir::Cache::pkgcache", "Dir::Cache::srcpkgcache")
	except:
		import platform

		un = platform.uname()
		aptVars = {
			"Dir::State::status": "/var/lib/dpkg/status",
			"APT::Architecture": architectureRemap[(un.system, un.machine)],
		}

	dpkgStatusFile = Path(aptVars["Dir::State::status"])
	assert dpkgStatusFile.is_file()
	etcDir = _getDir(aptVars, "Dir::Etc", fallbackEtcDir)
	aptLogDir = _getDir(aptVars, "Dir::Log", fallbackAptLogDir)
	aptStateDir = _getDir(aptVars, "Dir::State", fallbackAptStateDir)
	aptPackageCacheBase = _getDir(aptVars, "Dir::Cache", fallbackAptPackageCacheBase)

	sourcesListFile = etcDir / aptVars.get("Dir::Etc::sourcelist", fallbackSourcesListFileName)
	assert sourcesListFile.is_file()
	sourcesPartsDir = etcDir / aptVars.get("Dir::Etc::sourceparts", fallbackSourcesPartsDirName)
	assert sourcesPartsDir.is_dir()

	aptBinaryPackageCache = aptPackageCacheBase / aptVars.get("Dir::Cache::pkgcache", fallbackAptBinaryPackageCacheName)
	aptSourcePackageCache = aptPackageCacheBase / aptVars.get("Dir::Cache::srcpkgcache", fallbackAptSourcePackageCacheName)

	trustedKeyringPartsPath = aptVars.get("Dir::Etc::trustedparts", None)
	trustedFilesBase = etcDir
	if trustedKeyringPartsPath is None:
		try:
			trustedKeyringPartsPath = getHardcodedTrustedParts()
			trustedFilesBase = trustedKeyringPartsPath.parent
		except:
			trustedKeyringPartsPath = trustedFilesBase / fallbackTrustedKeyringPartsDirName
	else:
		trustedKeyringPartsPath = trustedFilesBase / trustedKeyringPartsPath
	assert trustedKeyringPartsPath.is_dir()

	trustedKeyringPath = aptVars.get("Apt::GPGV::TrustedKeyring", None)
	if trustedKeyringPath is None:
		trustedKeyringPath = aptVars.get("Dir::Etc::Trusted", fallbackTrustedKeyringFileName)
	trustedKeyringPath = trustedFilesBase / trustedKeyringPath
	assert trustedKeyringPath.is_file()

	return dpkgStatusFile, dpkgStatusFile.parent / "info", aptVars["APT::Architecture"], etcDir, sourcesListFile, sourcesPartsDir, trustedKeyringPath, trustedKeyringPartsPath, aptLogDir, aptStateDir, aptPackageCacheBase, aptBinaryPackageCache, aptSourcePackageCache


dpkgStatusFileLoc, dpkgInfoFilesLoc, defaultArch, etcDir, sourcesListFile, sourcesPartsDir, trustedKeyringPath, trustedKeyringPartsPath, aptLogDir, aptStateDir, aptPackageCacheBase, aptBinaryPackageCache, aptSourcePackageCache = getAptInfo()

trustedPartsRx = re.compile('^\\s*local\\s+TRUSTEDPARTS\\s*=\\s*"(/[\\w\\./]+)"$')


def getSigsInCaches():
	varLibListsDir = aptStateDir / "lists"
	return {f.name: f for f in list(varLibListsDir.glob("*_InRelease"))}


def readStatusFile():
	return debParse(dpkgStatusFileLoc).packages
