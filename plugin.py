import os
import shutil
import urllib.request
import zipfile

import sublime

# LSP
from LSP.plugin import AbstractPlugin, register_plugin, unregister_plugin

SESSION_NAME = "VHDL-ls"

# Update this single git tag to download a newer version.
#
# After changing this tag, go through the server settings again to see if any
# new server settings are added or old ones removed.
TAG = "v0.78.2"
URL = "https://github.com/VHDL-LS/rust_hdl/releases/download/{tag}/vhdl_ls-{arch}-{platform}.zip"
FOLDER = "vhdl_ls-{arch}-{platform}"


def arch() -> str:
    if sublime.arch() == "x64":
        return "x86_64"
    elif sublime.arch() == "x32":
        raise RuntimeError("Unsupported platform: 32-bit is not supported")
    elif sublime.arch() == "arm64":
        raise RuntimeError("Unsupported platform: ARM is not supported")
    else:
        raise RuntimeError("Unknown architecture: " + sublime.arch())


def platform() -> str:
    if sublime.platform() == "windows":
        return "pc-windows-msvc"
    else:
        return "unknown-linux-musl"


class LSP_VHDL_ls(AbstractPlugin):
    @classmethod
    def name(cls) -> str:
        return SESSION_NAME

    @classmethod
    def basedir(cls) -> str:
        return os.path.join(cls.storage_path(), __package__)

    @classmethod
    def server_version(cls) -> str:
        return TAG

    @classmethod
    def current_server_version(cls) -> str:
        with open(os.path.join(cls.basedir(), "VERSION"), "r") as fp:
            return fp.read()

    @classmethod
    def needs_update_or_installation(cls) -> bool:
        try:
            return cls.server_version() != cls.current_server_version()
        except OSError:
            return True

    @classmethod
    def install_or_update(cls) -> None:
        try:
            if os.path.isdir(cls.basedir()):
                shutil.rmtree(cls.basedir())
            os.makedirs(cls.basedir(), exist_ok=True)

            version = cls.server_version()
            url = URL.format(tag=TAG, arch=arch(), platform=platform())

            zip_path, _ = urllib.request.urlretrieve(url)
            with zipfile.ZipFile(zip_path, "r") as f:
                f.extractall(cls.basedir())

            folder = FOLDER.format(arch=arch(), platform=platform())
            shutil.move(os.path.join(cls.basedir(), folder, "bin"),
                os.path.join(cls.basedir(), "bin"))
            shutil.move(os.path.join(cls.basedir(), folder, "vhdl_libraries"),
                os.path.join(cls.basedir(), "vhdl_libraries"))
            os.rmdir(os.path.join(cls.basedir(), folder))

            serverfile = os.path.join(
                cls.basedir(),
                "bin/vhdl_ls.exe"
                if sublime.platform() == "windows"
                else "bin/vhdl_ls",
            )

            os.remove(zip_path)
            os.chmod(serverfile, 0o744)

            with open(os.path.join(cls.basedir(), "VERSION"), "w") as fp:
                fp.write(version)

        except BaseException:
            shutil.rmtree(cls.basedir(), ignore_errors=True)
            raise


def plugin_loaded() -> None:
    register_plugin(LSP_VHDL_ls)


def plugin_unloaded() -> None:
    unregister_plugin(LSP_VHDL_ls)
