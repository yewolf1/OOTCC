from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Iterator

PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
PROCESS_QUERY_INFORMATION = 0x0400

TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010

INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
MAX_PATH = 260

MEM_COMMIT = 0x00001000
PAGE_NOACCESS = 0x01
PAGE_GUARD = 0x100
PAGE_READWRITE = 0x04
PAGE_WRITECOPY = 0x08
PAGE_EXECUTE_READWRITE = 0x40
PAGE_EXECUTE_WRITECOPY = 0x80

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

OpenProcess = kernel32.OpenProcess
OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OpenProcess.restype = wintypes.HANDLE

ReadProcessMemory = kernel32.ReadProcessMemory
ReadProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
ReadProcessMemory.restype = wintypes.BOOL

WriteProcessMemory = kernel32.WriteProcessMemory
WriteProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.LPCVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
WriteProcessMemory.restype = wintypes.BOOL

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]
CloseHandle.restype = wintypes.BOOL

CreateToolhelp32Snapshot = kernel32.CreateToolhelp32Snapshot
CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
CreateToolhelp32Snapshot.restype = wintypes.HANDLE

Module32FirstW = kernel32.Module32FirstW
Module32FirstW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
Module32FirstW.restype = wintypes.BOOL

Module32NextW = kernel32.Module32NextW
Module32NextW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
Module32NextW.restype = wintypes.BOOL

VirtualQueryEx = kernel32.VirtualQueryEx
VirtualQueryEx.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, ctypes.c_void_p, ctypes.c_size_t]
VirtualQueryEx.restype = ctypes.c_size_t


class MODULEENTRY32W(ctypes.Structure):
    """Structure used by Toolhelp API to enumerate process modules."""
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("th32ModuleID", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("GlblcntUsage", wintypes.DWORD),
        ("ProccntUsage", wintypes.DWORD),
        ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
        ("modBaseSize", wintypes.DWORD),
        ("hModule", wintypes.HMODULE),
        ("szModule", wintypes.WCHAR * 256),
        ("szExePath", wintypes.WCHAR * MAX_PATH),
    ]


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    """Structure returned by VirtualQueryEx on 64-bit Windows."""
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("PartitionId", wintypes.WORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]


class WindowsProcessMemory:
    """Thin wrapper around WinAPI for reading and writing another process memory."""

    def __init__(self, pid: int) -> None:
        """Open the target process with full memory access rights."""
        self.pid = pid
        access = PROCESS_QUERY_INFORMATION | PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION
        self.handle = OpenProcess(access, False, pid)
        if not self.handle:
            raise OSError(ctypes.get_last_error(), "OpenProcess failed")

    def close(self) -> None:
        """Close the process handle."""
        if self.handle:
            CloseHandle(self.handle)
            self.handle = None

    def _check_read(self, ok: bool, read: ctypes.c_size_t, expected: int) -> None:
        if not ok or read.value != expected:
            raise OSError(ctypes.get_last_error(), "ReadProcessMemory failed")

    def _check_write(self, ok: bool, written: ctypes.c_size_t, expected: int, address: int) -> None:
        if not ok or written.value != expected:
            raise OSError(ctypes.get_last_error(), f"WriteProcessMemory failed at 0x{address:016X}")

    def read_u8(self, address: int) -> int:
        buffer = ctypes.c_uint8()
        read = ctypes.c_size_t()
        ok = ReadProcessMemory(self.handle, ctypes.c_void_p(address), ctypes.byref(buffer), ctypes.sizeof(buffer), ctypes.byref(read))
        self._check_read(ok, read, ctypes.sizeof(buffer))
        return int(buffer.value)

    def write_u8(self, address: int, value: int) -> None:
        buffer = ctypes.c_uint8(value)
        written = ctypes.c_size_t()
        ok = WriteProcessMemory(self.handle, ctypes.c_void_p(address), ctypes.byref(buffer), ctypes.sizeof(buffer), ctypes.byref(written))
        self._check_write(ok, written, ctypes.sizeof(buffer), address)

    def read_u16(self, address: int) -> int:
        buffer = ctypes.c_uint16()
        read = ctypes.c_size_t()
        ok = ReadProcessMemory(self.handle, ctypes.c_void_p(address), ctypes.byref(buffer), ctypes.sizeof(buffer), ctypes.byref(read))
        self._check_read(ok, read, ctypes.sizeof(buffer))
        return int(buffer.value)

    def write_u16(self, address: int, value: int) -> None:
        buffer = ctypes.c_uint16(value)
        written = ctypes.c_size_t()
        ok = WriteProcessMemory(self.handle, ctypes.c_void_p(address), ctypes.byref(buffer), ctypes.sizeof(buffer), ctypes.byref(written))
        self._check_write(ok, written, ctypes.sizeof(buffer), address)

    def read_i16(self, address: int) -> int:
        buffer = ctypes.c_int16()
        read = ctypes.c_size_t()
        ok = ReadProcessMemory(self.handle, ctypes.c_void_p(address), ctypes.byref(buffer), ctypes.sizeof(buffer), ctypes.byref(read))
        self._check_read(ok, read, ctypes.sizeof(buffer))
        return int(buffer.value)

    def write_i16(self, address: int, value: int) -> None:
        buffer = ctypes.c_int16(value)
        written = ctypes.c_size_t()
        ok = WriteProcessMemory(self.handle, ctypes.c_void_p(address), ctypes.byref(buffer), ctypes.sizeof(buffer), ctypes.byref(written))
        self._check_write(ok, written, ctypes.sizeof(buffer), address)

    def read_u32(self, address: int) -> int:
        buffer = ctypes.c_uint32()
        read = ctypes.c_size_t()
        ok = ReadProcessMemory(self.handle, ctypes.c_void_p(address), ctypes.byref(buffer), ctypes.sizeof(buffer), ctypes.byref(read))
        self._check_read(ok, read, ctypes.sizeof(buffer))
        return int(buffer.value)

    def write_u32(self, address: int, value: int) -> None:
        buffer = ctypes.c_uint32(value)
        written = ctypes.c_size_t()
        ok = WriteProcessMemory(self.handle, ctypes.c_void_p(address), ctypes.byref(buffer), ctypes.sizeof(buffer), ctypes.byref(written))
        self._check_write(ok, written, ctypes.sizeof(buffer), address)

    def read_bytes(self, address: int, size: int) -> bytes:
        buffer = (ctypes.c_ubyte * size)()
        read = ctypes.c_size_t()
        ok = ReadProcessMemory(self.handle, ctypes.c_void_p(address), ctypes.byref(buffer), size, ctypes.byref(read))
        self._check_read(ok, read, size)
        return bytes(buffer)

    def query_memory(self, address: int) -> MEMORY_BASIC_INFORMATION | None:
        info = MEMORY_BASIC_INFORMATION()
        result = VirtualQueryEx(self.handle, ctypes.c_void_p(address), ctypes.byref(info), ctypes.sizeof(info))
        if result == 0:
            return None
        return info

    def is_address_writable(self, address: int, size: int = 1) -> bool:
        info = self.query_memory(address)
        if info is None:
            return False
        protection = int(info.Protect)
        writable_flags = PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY
        if int(info.State) != MEM_COMMIT or protection & PAGE_GUARD or protection & PAGE_NOACCESS:
            return False
        if not protection & writable_flags:
            return False
        return address + size <= int(info.BaseAddress) + int(info.RegionSize)

    def iter_memory_regions(self, writable_only: bool = False) -> Iterator[tuple[int, int, int]]:
        """Yield committed readable regions, optionally only writable regions."""
        address = 0x10000
        max_address = 0x00007FFFFFFFFFFF
        writable_flags = PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY
        while address < max_address:
            info = self.query_memory(address)
            if info is None:
                address += 0x10000
                continue
            base = int(info.BaseAddress)
            size = int(info.RegionSize)
            protection = int(info.Protect)
            committed_readable = int(info.State) == MEM_COMMIT and not protection & PAGE_GUARD and not protection & PAGE_NOACCESS
            writable = committed_readable and bool(protection & writable_flags)
            if committed_readable and (not writable_only or writable):
                yield base, size, protection
            next_address = base + max(size, 0x1000)
            if next_address <= address:
                break
            address = next_address

    def get_module_info(self, module_name: str) -> tuple[int, int]:
        snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, self.pid)
        if snapshot == INVALID_HANDLE_VALUE:
            raise OSError(ctypes.get_last_error(), "CreateToolhelp32Snapshot failed")
        try:
            entry = MODULEENTRY32W()
            entry.dwSize = ctypes.sizeof(MODULEENTRY32W)
            ok = Module32FirstW(snapshot, ctypes.byref(entry))
            while ok:
                if entry.szModule.lower() == module_name.lower():
                    return ctypes.addressof(entry.modBaseAddr.contents), int(entry.modBaseSize)
                ok = Module32NextW(snapshot, ctypes.byref(entry))
        finally:
            CloseHandle(snapshot)
        raise RuntimeError(f"Module not found in target process: {module_name}")

    def get_module_base(self, module_name: str) -> int:
        base, _ = self.get_module_info(module_name)
        return base
