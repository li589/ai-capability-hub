from __future__ import annotations

import ctypes
import json
import os
import uuid
from ctypes import wintypes
from typing import Any


HRESULT = ctypes.c_long
UINT = ctypes.c_uint
SIZE_T = ctypes.c_size_t
STDMETHOD = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)

DXGI_ERROR_NOT_FOUND = 0x887A0002
DXGI_ADAPTER_FLAG_SOFTWARE = 0x2
ERROR_SUCCESS = 0
PDH_FMT_LARGE = 0x00000400


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    def __init__(self, guid: str) -> None:
        value = uuid.UUID(guid)
        super().__init__()
        self.Data1 = value.time_low
        self.Data2 = value.time_mid
        self.Data3 = value.time_hi_version
        self.Data4[:] = value.bytes[8:]


class LUID(ctypes.Structure):
    _fields_ = [
        ("LowPart", wintypes.DWORD),
        ("HighPart", wintypes.LONG),
    ]


class DXGI_ADAPTER_DESC1(ctypes.Structure):
    _fields_ = [
        ("Description", ctypes.c_wchar * 128),
        ("VendorId", UINT),
        ("DeviceId", UINT),
        ("SubSysId", UINT),
        ("Revision", UINT),
        ("DedicatedVideoMemory", SIZE_T),
        ("DedicatedSystemMemory", SIZE_T),
        ("SharedSystemMemory", SIZE_T),
        ("AdapterLuid", LUID),
        ("Flags", UINT),
    ]


class PDH_FMT_COUNTERVALUE_VALUE(ctypes.Union):
    _fields_ = [
        ("longValue", wintypes.LONG),
        ("doubleValue", ctypes.c_double),
        ("largeValue", ctypes.c_longlong),
        ("AnsiStringValue", ctypes.c_char_p),
        ("WideStringValue", wintypes.LPWSTR),
    ]


class PDH_FMT_COUNTERVALUE(ctypes.Structure):
    _fields_ = [
        ("CStatus", wintypes.DWORD),
        ("value", PDH_FMT_COUNTERVALUE_VALUE),
    ]


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


IID_IDXGI_FACTORY1 = GUID("770aae78-f26f-4dba-a829-253c83d1b387")


def _failed(status: int) -> bool:
    return (int(status) & 0x80000000) != 0


def _hresult_code(hresult: int) -> int:
    return int(hresult) & 0xFFFFFFFF


def _com_method(pointer: ctypes.c_void_p, index: int, restype: Any, *argtypes: Any) -> Any:
    vtable = ctypes.cast(pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    return STDMETHOD(restype, ctypes.c_void_p, *argtypes)(vtable[index])


def _release(pointer: ctypes.c_void_p | None) -> None:
    if not pointer:
        return
    release = _com_method(pointer, 2, wintypes.ULONG)
    release(pointer)


def _pdh_status(status: int) -> int:
    return int(status) & 0xFFFFFFFF


def _read_system_memory() -> dict[str, int]:
    memory_status = MEMORYSTATUSEX()
    memory_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)

    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory_status)):
        raise ctypes.WinError()

    return {
        "sys_mem_total": int(memory_status.ullTotalPhys),
        "sys_mem_free": int(memory_status.ullAvailPhys),
    }


def _bytes_to_gb(value: int) -> float:
    return round(value / (1024**3), 2)


def _read_pdh_counters(counter_paths: dict[str, str]) -> dict[str, int]:
    if not counter_paths:
        return {}

    pdh = ctypes.WinDLL("pdh")
    open_query = pdh.PdhOpenQueryW
    open_query.argtypes = [wintypes.LPCWSTR, ctypes.c_size_t, ctypes.POINTER(wintypes.HANDLE)]
    open_query.restype = wintypes.LONG

    add_counter = getattr(pdh, "PdhAddEnglishCounterW", pdh.PdhAddCounterW)
    add_counter.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR, ctypes.c_size_t, ctypes.POINTER(wintypes.HANDLE)]
    add_counter.restype = wintypes.LONG

    collect_query_data = pdh.PdhCollectQueryData
    collect_query_data.argtypes = [wintypes.HANDLE]
    collect_query_data.restype = wintypes.LONG

    get_counter_value = pdh.PdhGetFormattedCounterValue
    get_counter_value.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(PDH_FMT_COUNTERVALUE),
    ]
    get_counter_value.restype = wintypes.LONG

    close_query = pdh.PdhCloseQuery
    close_query.argtypes = [wintypes.HANDLE]
    close_query.restype = wintypes.LONG

    query = wintypes.HANDLE()
    status = open_query(None, 0, ctypes.byref(query))
    if _pdh_status(status) != ERROR_SUCCESS:
        return {}

    counter_handles: dict[str, wintypes.HANDLE] = {}
    try:
        for name, path in counter_paths.items():
            counter = wintypes.HANDLE()
            status = add_counter(query, path, 0, ctypes.byref(counter))
            if _pdh_status(status) == ERROR_SUCCESS:
                counter_handles[name] = counter

        if not counter_handles:
            return {}

        status = collect_query_data(query)
        if _pdh_status(status) != ERROR_SUCCESS:
            return {}

        values: dict[str, int] = {}
        for name, counter in counter_handles.items():
            counter_type = wintypes.DWORD()
            value = PDH_FMT_COUNTERVALUE()
            status = get_counter_value(
                counter,
                PDH_FMT_LARGE,
                ctypes.byref(counter_type),
                ctypes.byref(value),
            )
            if _pdh_status(status) == ERROR_SUCCESS and _pdh_status(value.CStatus) == ERROR_SUCCESS:
                values[name] = int(value.value.largeValue)

        return values
    finally:
        close_query(query)


def _adapter_luid_instance(desc: DXGI_ADAPTER_DESC1) -> str:
    high_part = int(desc.AdapterLuid.HighPart) & 0xFFFFFFFF
    low_part = int(desc.AdapterLuid.LowPart) & 0xFFFFFFFF
    return f"luid_0x{high_part:08x}_0x{low_part:08x}_phys_0"


def _read_adapter_memory_usage(desc: DXGI_ADAPTER_DESC1) -> dict[str, int]:
    instance = _adapter_luid_instance(desc)
    part_instance = f"{instance}_part_0"
    return _read_pdh_counters(
        {
            "dedicated_usage": rf"\GPU Adapter Memory({instance})\Dedicated Usage",
            "shared_usage": rf"\GPU Adapter Memory({instance})\Shared Usage",
            "total_committed": rf"\GPU Adapter Memory({instance})\Total Committed",
            "local_usage": rf"\GPU Local Adapter Memory({part_instance})\Local Usage",
            "non_local_usage": rf"\GPU Non Local Adapter Memory({part_instance})\Non Local Usage",
        }
    )


def _collect_gpu_memory_info(include_software: bool = False) -> list[dict[str, Any]]:
    if os.name != "nt":
        raise OSError("此脚本只能在 Windows 上获取 DXGI GPU 显存信息")

    dxgi = ctypes.WinDLL("dxgi")
    create_factory = dxgi.CreateDXGIFactory1
    create_factory.argtypes = [ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)]
    create_factory.restype = HRESULT

    factory = ctypes.c_void_p()
    hresult = create_factory(ctypes.byref(IID_IDXGI_FACTORY1), ctypes.byref(factory))
    if _failed(hresult):
        raise OSError(f"CreateDXGIFactory1 失败: 0x{_hresult_code(hresult):08X}")

    adapters: list[dict[str, Any]] = []
    try:
        enum_adapters = _com_method(
            factory,
            12,
            HRESULT,
            UINT,
            ctypes.POINTER(ctypes.c_void_p),
        )
        index = 0

        while True:
            adapter = ctypes.c_void_p()
            hresult = enum_adapters(factory, index, ctypes.byref(adapter))
            if _hresult_code(hresult) == DXGI_ERROR_NOT_FOUND:
                break
            if _failed(hresult):
                raise OSError(f"EnumAdapters1({index}) 失败: 0x{_hresult_code(hresult):08X}")

            try:
                get_desc = _com_method(
                    adapter,
                    10,
                    HRESULT,
                    ctypes.POINTER(DXGI_ADAPTER_DESC1),
                )
                desc = DXGI_ADAPTER_DESC1()
                hresult = get_desc(adapter, ctypes.byref(desc))
                if _failed(hresult):
                    raise OSError(f"GetDesc1({index}) 失败: 0x{_hresult_code(hresult):08X}")

                is_software_adapter = bool(desc.Flags & DXGI_ADAPTER_FLAG_SOFTWARE)
                if is_software_adapter and not include_software:
                    index += 1
                    continue

                memory_usage = _read_adapter_memory_usage(desc)
                dedicated_used = memory_usage.get("dedicated_usage")
                shared_used = memory_usage.get("shared_usage")
                total_used = None
                if dedicated_used is not None or shared_used is not None:
                    total_used = (dedicated_used or 0) + (shared_used or 0)

                dedicated_total = int(desc.DedicatedVideoMemory)
                shared_total = int(desc.SharedSystemMemory)
                adapters.append(
                    {
                        "name": desc.Description.rstrip("\x00"),
                        "vendor_id": int(desc.VendorId),
                        "device_id": int(desc.DeviceId),
                        "is_software_adapter": is_software_adapter,
                        "dedicated_vram_total": dedicated_total,
                        "shared_gpu_memory_total": shared_total,
                        "gpu_memory_total": dedicated_total + shared_total,
                        "dedicated_vram_used": dedicated_used,
                        "shared_gpu_memory_used": shared_used,
                        "gpu_memory_used": total_used,
                        "driver_total_committed": memory_usage.get("total_committed"),
                        "local_adapter_memory_used": memory_usage.get("local_usage"),
                        "non_local_adapter_memory_used": memory_usage.get("non_local_usage"),
                    }
                )
            finally:
                _release(adapter)

            index += 1
    finally:
        _release(factory)

    return adapters


def get_gpu_memory_win() -> dict[str, float]:
    gpu_infos = _collect_gpu_memory_info(include_software=False)
    intel_gpu = next(
        (gpu_info for gpu_info in gpu_infos if gpu_info["name"].strip().lower().startswith("intel")),
        None,
    )
    if intel_gpu is None:
        raise RuntimeError("未找到名称以 Intel 开头的 GPU")

    gpu_mem_total = int(intel_gpu["gpu_memory_total"])
    gpu_mem_used = intel_gpu["gpu_memory_used"]
    if gpu_mem_used is None:
        raise RuntimeError(f"未能获取 GPU 已用显存: {intel_gpu['name']}")

    system_memory = _read_system_memory()
    return {
        "sys_mem_total": _bytes_to_gb(system_memory["sys_mem_total"]),
        "sys_mem_free": _bytes_to_gb(system_memory["sys_mem_free"]),
        "gpu_mem_total": _bytes_to_gb(gpu_mem_total),
        "gpu_mem_free": _bytes_to_gb(max(gpu_mem_total - int(gpu_mem_used), 0)),
    }

if __name__ == "__main__":
    print(json.dumps(get_gpu_memory_win(), ensure_ascii=False, indent=4))