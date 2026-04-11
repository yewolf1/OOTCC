from __future__ import annotations

import ctypes
from ctypes import wintypes


# --- Access flags for OpenProcess ---
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
PROCESS_QUERY_INFORMATION = 0x0400

# --- Toolhelp snapshot flags ---
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010

INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
MAX_PATH = 260

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# --- WinAPI bindings ---
OpenProcess = kernel32.OpenProcess
OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OpenProcess.restype = wintypes.HANDLE

ReadProcessMemory = kernel32.ReadProcessMemory
ReadProcessMemory.argtypes = [
    wintypes.HANDLE,
    wintypes.LPCVOID,
    wintypes.LPVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
ReadProcessMemory.restype = wintypes.BOOL

WriteProcessMemory = kernel32.WriteProcessMemory
WriteProcessMemory.argtypes = [
    wintypes.HANDLE,
    wintypes.LPVOID,
    wintypes.LPCVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
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


class WindowsProcessMemory:
    """Thin wrapper around WinAPI for reading and writing another process memory."""

    def __init__(self, pid: int) -> None:
        """Open the target process with full memory access rights."""
        self.pid = pid

        # Required rights for reading + writing + resolving modules
        access = (
            PROCESS_QUERY_INFORMATION
            | PROCESS_VM_READ
            | PROCESS_VM_WRITE
            | PROCESS_VM_OPERATION
        )

        self.handle = OpenProcess(access, False, pid)
        if not self.handle:
            raise OSError(ctypes.get_last_error(), "OpenProcess failed")

    def close(self) -> None:
        """Close the process handle."""
        if self.handle:
            CloseHandle(self.handle)
            self.handle = None

    def read_u8(self, address: int) -> int:
        """Read an unsigned byte."""
        buffer = ctypes.c_uint8()
        read = ctypes.c_size_t()

        ok = ReadProcessMemory(
            self.handle,
            ctypes.c_void_p(address),
            ctypes.byref(buffer),
            ctypes.sizeof(buffer),
            ctypes.byref(read),
        )

        if not ok:
            raise OSError(ctypes.get_last_error())

        return int(buffer.value)

    def write_u8(self, address: int, value: int) -> None:
        """Write an unsigned byte."""
        buffer = ctypes.c_uint8(value)
        written = ctypes.c_size_t()

        ok = WriteProcessMemory(
            self.handle,
            ctypes.c_void_p(address),
            ctypes.byref(buffer),
            ctypes.sizeof(buffer),
            ctypes.byref(written),
        )

        if not ok:
            raise OSError(ctypes.get_last_error())

    def read_u32(self, address: int) -> int:
        """Read an unsigned 32-bit value."""
        buffer = ctypes.c_uint32()
        read = ctypes.c_size_t()
        ReadProcessMemory(self.handle, address, ctypes.byref(buffer), 4, ctypes.byref(read))
        return buffer.value

    def write_u32(self, address: int, value: int):
        """Write an unsigned 32-bit value."""
        buffer = ctypes.c_uint32(value)
        written = ctypes.c_size_t()
        WriteProcessMemory(self.handle, address, ctypes.byref(buffer), 4, ctypes.byref(written))

    def read_u16(self, address: int) -> int:
        """Read an unsigned 16-bit value."""
        buffer = ctypes.c_uint16()
        read = ctypes.c_size_t()

        ok = ReadProcessMemory(
            self.handle,
            ctypes.c_void_p(address),
            ctypes.byref(buffer),
            ctypes.sizeof(buffer),
            ctypes.byref(read),
        )

        if not ok or read.value != ctypes.sizeof(buffer):
            raise OSError(ctypes.get_last_error(), "ReadProcessMemory failed")

        return int(buffer.value)

    def write_u16(self, address: int, value: int) -> None:
        """Write an unsigned 16-bit value."""
        buffer = ctypes.c_uint16(value)
        written = ctypes.c_size_t()

        ok = WriteProcessMemory(
            self.handle,
            ctypes.c_void_p(address),
            ctypes.byref(buffer),
            ctypes.sizeof(buffer),
            ctypes.byref(written),
        )

        if not ok or written.value != ctypes.sizeof(buffer):
            raise OSError(ctypes.get_last_error(), "WriteProcessMemory failed")

    def read_i16(self, address: int) -> int:
        """Read a signed 16-bit value."""
        buffer = ctypes.c_int16()
        read = ctypes.c_size_t()

        ok = ReadProcessMemory(
            self.handle,
            ctypes.c_void_p(address),
            ctypes.byref(buffer),
            ctypes.sizeof(buffer),
            ctypes.byref(read),
        )

        if not ok or read.value != ctypes.sizeof(buffer):
            raise OSError(ctypes.get_last_error(), "ReadProcessMemory failed")

        return int(buffer.value)

    def write_i16(self, address: int, value: int) -> None:
        """Write a signed 16-bit value."""
        buffer = ctypes.c_int16(value)
        written = ctypes.c_size_t()

        ok = WriteProcessMemory(
            self.handle,
            ctypes.c_void_p(address),
            ctypes.byref(buffer),
            ctypes.sizeof(buffer),
            ctypes.byref(written),
        )

        if not ok or written.value != ctypes.sizeof(buffer):
            raise OSError(ctypes.get_last_error(), "WriteProcessMemory failed")

    def get_module_base(self, module_name: str) -> int:
        """
        Resolve the base address of a module inside the target process.

        Uses Toolhelp snapshot enumeration.
        This is required for module_offset strategies.
        """
        snapshot = CreateToolhelp32Snapshot(
            TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32,
            self.pid,
        )

        if snapshot == INVALID_HANDLE_VALUE:
            raise OSError(ctypes.get_last_error(), "CreateToolhelp32Snapshot failed")

        try:
            entry = MODULEENTRY32W()
            entry.dwSize = ctypes.sizeof(MODULEENTRY32W)

            ok = Module32FirstW(snapshot, ctypes.byref(entry))

            while ok:
                if entry.szModule.lower() == module_name.lower():
                    return ctypes.addressof(entry.modBaseAddr.contents)

                ok = Module32NextW(snapshot, ctypes.byref(entry))

        finally:
            # Critical: always release snapshot handle to avoid leaks
            CloseHandle(snapshot)

        raise RuntimeError(f"Module not found in target process: {module_name}")