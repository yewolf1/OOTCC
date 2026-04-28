from __future__ import annotations

import ctypes
from ctypes import wintypes
from pathlib import Path


dbghelp = ctypes.WinDLL("dbghelp", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

MAX_SYM_NAME = 1024
SYMOPT_UNDNAME = 0x00000002
SYMOPT_DEFERRED_LOADS = 0x00000004
SYMOPT_LOAD_LINES = 0x00000010
SYMOPT_FAIL_CRITICAL_ERRORS = 0x00000200
SYMOPT_EXACT_SYMBOLS = 0x00000400


class SYMBOL_INFO(ctypes.Structure):
    _fields_ = [
        ("SizeOfStruct", wintypes.ULONG),
        ("TypeIndex", wintypes.ULONG),
        ("Reserved", ctypes.c_ulonglong * 2),
        ("Index", wintypes.ULONG),
        ("Size", wintypes.ULONG),
        ("ModBase", ctypes.c_ulonglong),
        ("Flags", wintypes.ULONG),
        ("Value", ctypes.c_ulonglong),
        ("Address", ctypes.c_ulonglong),
        ("Register", wintypes.ULONG),
        ("Scope", wintypes.ULONG),
        ("Tag", wintypes.ULONG),
        ("NameLen", wintypes.ULONG),
        ("MaxNameLen", wintypes.ULONG),
        ("Name", ctypes.c_char * MAX_SYM_NAME),
    ]


GetCurrentProcess = kernel32.GetCurrentProcess
GetCurrentProcess.argtypes = []
GetCurrentProcess.restype = wintypes.HANDLE

SymSetOptions = dbghelp.SymSetOptions
SymSetOptions.argtypes = [wintypes.DWORD]
SymSetOptions.restype = wintypes.DWORD

SymInitialize = dbghelp.SymInitialize
SymInitialize.argtypes = [wintypes.HANDLE, ctypes.c_char_p, wintypes.BOOL]
SymInitialize.restype = wintypes.BOOL

SymCleanup = dbghelp.SymCleanup
SymCleanup.argtypes = [wintypes.HANDLE]
SymCleanup.restype = wintypes.BOOL

SymLoadModuleExW = dbghelp.SymLoadModuleExW
SymLoadModuleExW.argtypes = [
    wintypes.HANDLE,
    wintypes.HANDLE,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    ctypes.c_ulonglong,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
]
SymLoadModuleExW.restype = ctypes.c_ulonglong

SymFromName = dbghelp.SymFromName
SymFromName.argtypes = [wintypes.HANDLE, ctypes.c_char_p, ctypes.POINTER(SYMBOL_INFO)]
SymFromName.restype = wintypes.BOOL

SymEnumSymbols = dbghelp.SymEnumSymbols
SymEnumSymbols.restype = wintypes.BOOL

PSYM_ENUMERATESYMBOLS_CALLBACK = ctypes.WINFUNCTYPE(
    wintypes.BOOL,
    ctypes.POINTER(SYMBOL_INFO),
    wintypes.ULONG,
    ctypes.c_void_p,
)
SymEnumSymbols.argtypes = [
    wintypes.HANDLE,
    ctypes.c_ulonglong,
    ctypes.c_char_p,
    PSYM_ENUMERATESYMBOLS_CALLBACK,
    ctypes.c_void_p,
]


class PdbSymbolResolver:
    """Resolve SoH global addresses from the PDB matching the loaded soh.exe module."""

    def __init__(self, image_path: str, module_base: int, module_size: int) -> None:
        self.image_path = str(image_path)
        self.module_base = int(module_base)
        self.module_size = int(module_size)
        self._handle = GetCurrentProcess()
        self._loaded = False

    def __enter__(self) -> "PdbSymbolResolver":
        self.load()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.cleanup()

    def load(self) -> None:
        image = Path(self.image_path)
        search_dirs = [str(image.parent), str(image.parent / "debug")]
        search_path = ";".join(search_dirs).encode("mbcs", errors="ignore")
        SymSetOptions(SYMOPT_UNDNAME | SYMOPT_DEFERRED_LOADS | SYMOPT_LOAD_LINES | SYMOPT_FAIL_CRITICAL_ERRORS | SYMOPT_EXACT_SYMBOLS)
        if not SymInitialize(self._handle, search_path, False):
            raise OSError(ctypes.get_last_error(), "SymInitialize failed")
        loaded_base = SymLoadModuleExW(
            self._handle,
            None,
            self.image_path,
            None,
            self.module_base,
            self.module_size,
            None,
            0,
        )
        if not loaded_base:
            error = ctypes.get_last_error()
            SymCleanup(self._handle)
            raise OSError(error, "SymLoadModuleExW failed")
        self._loaded = True

    def cleanup(self) -> None:
        if self._loaded:
            SymCleanup(self._handle)
            self._loaded = False

    def address_of_any(self, names: list[str]) -> int | None:
        for name in names:
            address = self.address_of(name)
            if address is not None:
                return address
        return None

    def address_of(self, name: str) -> int | None:
        info = SYMBOL_INFO()
        info.SizeOfStruct = ctypes.sizeof(SYMBOL_INFO) - MAX_SYM_NAME + 1
        info.MaxNameLen = MAX_SYM_NAME - 1
        ok = SymFromName(self._handle, name.encode("ascii"), ctypes.byref(info))
        if ok:
            return int(info.Address)
        return None

    def _read_symbol_name(self, symbol_info: ctypes.POINTER(SYMBOL_INFO)) -> str:
        name_len = int(symbol_info.contents.NameLen)
        if name_len <= 0:
            return ""
        max_len = min(name_len, MAX_SYM_NAME - 1)
        name_address = ctypes.addressof(symbol_info.contents) + SYMBOL_INFO.Name.offset
        raw_name = ctypes.string_at(name_address, max_len)
        return raw_name.decode("utf-8", errors="ignore")

    def matching_addresses(self, masks: list[str], contains: list[str]) -> list[tuple[str, int]]:
        contains_lower = [value.lower() for value in contains]
        matches: list[tuple[str, int]] = []

        def callback(symbol_info, symbol_size, context):
            name = self._read_symbol_name(symbol_info)
            lowered = name.lower()
            address = int(symbol_info.contents.Address)
            if address and all(value in lowered for value in contains_lower):
                matches.append((name, address))
            return True

        cb = PSYM_ENUMERATESYMBOLS_CALLBACK(callback)
        for mask in masks:
            SymEnumSymbols(self._handle, self.module_base, mask.encode("ascii"), cb, None)
        unique: dict[int, str] = {}
        for name, address in matches:
            unique.setdefault(address, name)
        return sorted(((name, address) for address, name in unique.items()), key=lambda item: (len(item[0]), item[0]))

    def find_first_matching(self, masks: list[str], contains: list[str]) -> int | None:
        contains_lower = [value.lower() for value in contains]
        matches: list[tuple[str, int]] = []

        def callback(symbol_info, symbol_size, context):
            name = self._read_symbol_name(symbol_info)
            lowered = name.lower()
            if all(value in lowered for value in contains_lower):
                matches.append((name, int(symbol_info.contents.Address)))
            return True

        cb = PSYM_ENUMERATESYMBOLS_CALLBACK(callback)
        for mask in masks:
            SymEnumSymbols(self._handle, self.module_base, mask.encode("ascii"), cb, None)
            if matches:
                matches.sort(key=lambda item: (len(item[0]), item[0]))
                return matches[0][1]
        return None
