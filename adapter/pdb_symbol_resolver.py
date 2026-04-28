from __future__ import annotations

import ctypes
from pathlib import Path

from adapter.windows_memory import WindowsProcessMemory

MAX_SYM_NAME = 1024
SYMOPT_UNDNAME = 0x00000002
SYMOPT_DEFERRED_LOADS = 0x00000004
SYMOPT_LOAD_LINES = 0x00000010

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
dbghelp = ctypes.WinDLL("dbghelp", use_last_error=True)

SymInitializeW = dbghelp.SymInitializeW
SymInitializeW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_bool]
SymInitializeW.restype = ctypes.c_bool

SymCleanup = dbghelp.SymCleanup
SymCleanup.argtypes = [ctypes.c_void_p]
SymCleanup.restype = ctypes.c_bool

SymSetOptions = dbghelp.SymSetOptions
SymSetOptions.argtypes = [ctypes.c_uint32]
SymSetOptions.restype = ctypes.c_uint32

SymLoadModuleExW = dbghelp.SymLoadModuleExW
SymLoadModuleExW.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_wchar_p,
    ctypes.c_wchar_p,
    ctypes.c_uint64,
    ctypes.c_uint32,
    ctypes.c_void_p,
    ctypes.c_uint32,
]
SymLoadModuleExW.restype = ctypes.c_uint64

SymFromNameW = dbghelp.SymFromNameW
SymFromNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_void_p]
SymFromNameW.restype = ctypes.c_bool


class SYMBOL_INFOW(ctypes.Structure):
    _fields_ = [
        ("SizeOfStruct", ctypes.c_uint32),
        ("TypeIndex", ctypes.c_uint32),
        ("Reserved", ctypes.c_uint64 * 2),
        ("Index", ctypes.c_uint32),
        ("Size", ctypes.c_uint32),
        ("ModBase", ctypes.c_uint64),
        ("Flags", ctypes.c_uint32),
        ("Value", ctypes.c_uint64),
        ("Address", ctypes.c_uint64),
        ("Register", ctypes.c_uint32),
        ("Scope", ctypes.c_uint32),
        ("Tag", ctypes.c_uint32),
        ("NameLen", ctypes.c_uint32),
        ("MaxNameLen", ctypes.c_uint32),
        ("Name", ctypes.c_wchar * MAX_SYM_NAME),
    ]


class PdbSymbolResolver:
    def __init__(self, memory: WindowsProcessMemory, exe_path: str) -> None:
        self.memory = memory
        self.exe_path = str(Path(exe_path))
        self._initialized = False
        self._module_loaded = False
        self._initialize()

    def close(self) -> None:
        if self._initialized:
            SymCleanup(self.memory.handle)
            self._initialized = False

    def __enter__(self) -> "PdbSymbolResolver":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _initialize(self) -> None:
        exe = Path(self.exe_path)
        search_parts = [str(exe.parent)]
        debug_dir = exe.parent / "debug"
        if debug_dir.exists():
            search_parts.append(str(debug_dir))
        search_path = ";".join(search_parts)

        SymSetOptions(SYMOPT_UNDNAME | SYMOPT_DEFERRED_LOADS | SYMOPT_LOAD_LINES)
        if not SymInitializeW(self.memory.handle, search_path, False):
            raise OSError(ctypes.get_last_error(), "SymInitializeW failed")
        self._initialized = True

        module_base, module_size = self.memory.get_module_info(exe.name)
        loaded_base = SymLoadModuleExW(
            self.memory.handle,
            None,
            str(exe),
            exe.name,
            ctypes.c_uint64(module_base).value,
            ctypes.c_uint32(module_size).value,
            None,
            0,
        )
        if loaded_base == 0:
            raise OSError(ctypes.get_last_error(), "SymLoadModuleExW failed")
        self._module_loaded = True

    def find_first(self, names: list[str]) -> int | None:
        for name in names:
            address = self.find_exact(name)
            if address is not None:
                return address
        return None

    def find_exact(self, name: str) -> int | None:
        symbol = SYMBOL_INFOW()
        symbol.SizeOfStruct = ctypes.sizeof(SYMBOL_INFOW) - ctypes.sizeof(ctypes.c_wchar) * MAX_SYM_NAME
        symbol.MaxNameLen = MAX_SYM_NAME
        ok = SymFromNameW(self.memory.handle, name, ctypes.byref(symbol))
        if not ok:
            return None
        return int(symbol.Address)
