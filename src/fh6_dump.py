# -*- coding: utf-8 -*-
"""从运行中的 Forza Horizon 6 进程内存导出当前彩绘组为原始 FH6 JSON。

基于 FH5 forza-painter 的 -dump（签名 + 指针链）与 bvzrays/forza-painter-fh6
的 typecode probe/export（图层解码偏移）。修复点：
  * 进程名大小写不敏感，兼容 ForzaHorizon6.exe / ForzaHorizon6-Win64-Shipping.exe 等；
  * 定位“当前打开彩绘组”（任意图层数），不再依赖 1000 个圆形控制模板；
  * 签名 + 指针链为主，暴力扫描为兜底。
只依赖标准库 ctypes，不引入 psutil / pywin32。
"""
from __future__ import annotations
import ctypes
import math
import struct
import time
from ctypes import wintypes
from typing import Any, Dict, List, Optional, Tuple

SIGNATURE = b"\x12\x47\x9B\x13\x29\xD9\xA2\xB1"
SIG_SCAN_START = 0x08000000
SIG_SCAN_SIZE = 0x02000000
OFF_ROOT = 0xB8
OFF_EDITOR = 0xA58
OFF_LIVERY = 0x8
OFF_GROUP = 0x20
OFF_COUNT = 0x5A
OFF_TABLE = 0x78
OFF_TABLE_END = 0x80
OFF_TABLE_CAPACITY = 0x88
OFF_POS = 0x18
OFF_SCALE = 0x28
OFF_ROT = 0x50
OFF_SKEW = 0x70
OFF_COLOR = 0x74
OFF_MASK = 0x78
OFF_SHAPE = 0x7A
LAYER_SIZE = 0x140
LAYER_SAFE_SIZE = 0xC0
MIN_LAYER_SIZE = 0x7C
TYPE_CODE_BASE = 0x100000
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
TH32CS_SNAPPROCESS = 0x00000002
MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01
RW_MASK = 0xCC
MAX_COUNT = 5000
DEFAULT_SCAN_TIMEOUT = 180.0
CHUNK_SIZE = 8 * 1024 * 1024
# 当前 FH6 版本彩绘组对象的 vtable RVA（相对游戏主模块基址，运行时 = base + RVA）。
# 从 Forza Paint Studio 与实机内存分析得到；游戏更新后可能需要重新校准。
GROUP_VTABLE_RVA = 0x6868770
# 候选组头偏移（FH6 实际结构可能与 FH5/旧探针不同，运行时逐个尝试并按图层解码结果筛选）
COUNT_OFFSETS = (0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48, 0x50, 0x58, 0x5A, 0x60, 0x68, 0x70, 0x78, 0x80)
TABLE_OFFSETS = (0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48, 0x50, 0x58, 0x60, 0x68, 0x70, 0x78, 0x80, 0x88, 0x90, 0x98, 0xA0, 0xA8, 0xB0, 0xB8, 0xC0, 0xC8, 0xD0)


class Fh6DumpError(RuntimeError):
    pass


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_char * 260),
    ]


class MODULEINFO(ctypes.Structure):
    _fields_ = [
        ("lpBaseOfDll", ctypes.c_void_p),
        ("SizeOfImage", wintypes.DWORD),
        ("EntryPoint", ctypes.c_void_p),
    ]


class MBI(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", wintypes.LPVOID),
        ("AllocationBase", wintypes.LPVOID),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)
kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
kernel32.CreateToolhelp32Snapshot.argtypes = (wintypes.DWORD, wintypes.DWORD)
kernel32.Process32First.argtypes = (wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32))
kernel32.Process32Next.argtypes = (wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32))
kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
kernel32.ReadProcessMemory.restype = wintypes.BOOL
kernel32.ReadProcessMemory.argtypes = (
    wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t),
)
kernel32.VirtualQueryEx.restype = ctypes.c_size_t
kernel32.VirtualQueryEx.argtypes = (wintypes.HANDLE, wintypes.LPCVOID, ctypes.POINTER(MBI), ctypes.c_size_t)
psapi.EnumProcessModules.argtypes = (
    wintypes.HANDLE, ctypes.POINTER(wintypes.HMODULE), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
)
psapi.GetModuleInformation.argtypes = (
    wintypes.HANDLE, wintypes.HMODULE, ctypes.POINTER(MODULEINFO), wintypes.DWORD,
)


def _find_pid() -> int:
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if not snapshot or snapshot == wintypes.HANDLE(-1).value:
        raise Fh6DumpError("无法枚举系统进程。")
    entry = PROCESSENTRY32()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
    try:
        if not kernel32.Process32First(snapshot, ctypes.byref(entry)):
            raise Fh6DumpError("无法枚举系统进程。")
        while True:
            name = entry.szExeFile.decode("utf-8", errors="ignore").lower()
            if "forzahorizon6" in name:
                return int(entry.th32ProcessID)
            if not kernel32.Process32Next(snapshot, ctypes.byref(entry)):
                break
    finally:
        kernel32.CloseHandle(snapshot)
    raise Fh6DumpError("未找到 ForzaHorizon6.exe 进程，请确认游戏正在运行。")


def _open_process(pid: int) -> int:
    handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, int(pid))
    if not handle:
        raise Fh6DumpError("无法打开 ForzaHorizon6 进程（可能权限不足，请以管理员身份运行本工具）。")
    return handle


def _read(handle: int, address: int, size: int) -> bytes:
    if size <= 0 or not address:
        return b""
    buf = ctypes.create_string_buffer(size)
    read = ctypes.c_size_t(0)
    ok = kernel32.ReadProcessMemory(handle, int(address), buf, int(size), ctypes.byref(read))
    if not ok or read.value <= 0:
        return b""
    return buf.raw[: read.value]


def _read_u16(handle: int, address: int) -> int:
    raw = _read(handle, address, 2)
    return struct.unpack("<H", raw)[0] if len(raw) == 2 else 0


def _read_u64(handle: int, address: int) -> int:
    raw = _read(handle, address, 8)
    return struct.unpack("<Q", raw)[0] if len(raw) == 8 else 0


def _module_info(handle: int) -> Tuple[int, int]:
    modules = (wintypes.HMODULE * 256)()
    needed = wintypes.DWORD(0)
    if not psapi.EnumProcessModules(handle, modules, ctypes.sizeof(modules), ctypes.byref(needed)):
        raise Fh6DumpError("无法枚举游戏模块。")
    info = MODULEINFO()
    if not psapi.GetModuleInformation(handle, modules[0], ctypes.byref(info), ctypes.sizeof(info)):
        raise Fh6DumpError("无法获取游戏主模块信息。")
    return int(info.lpBaseOfDll or 0), int(info.SizeOfImage or 0)


def _is_plausible_ptr(value: int) -> bool:
    return 0x10000 <= value <= 0x7FFFFFFFFFFF


def _safe_float(value: Any) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return value


def layer_plausible(raw: bytes) -> bool:
    """定位用严格校验：浮点有限且 shape word 在 1..0x1FFF。"""
    if len(raw) < MIN_LAYER_SIZE:
        return False
    x, y = struct.unpack_from("<ff", raw, OFF_POS)
    sx, sy = struct.unpack_from("<ff", raw, OFF_SCALE)
    rotation = struct.unpack_from("<f", raw, OFF_ROT)[0]
    skew = struct.unpack_from("<f", raw, OFF_SKEW)[0]
    shape_word = struct.unpack_from("<H", raw, OFF_SHAPE)[0]
    if not all(math.isfinite(v) and -1000000.0 <= v <= 1000000.0 for v in (x, y, sx, sy, rotation, skew)):
        return False
    return 1 <= shape_word <= 0x1FFF


def decode_layer(raw: bytes) -> Optional[Dict[str, Any]]:
    """导出用宽松解码：保留所有可读图层，非有限浮点钳制为 0。"""
    if len(raw) < MIN_LAYER_SIZE:
        return None
    x, y = struct.unpack_from("<ff", raw, OFF_POS)
    sx, sy = struct.unpack_from("<ff", raw, OFF_SCALE)
    rotation = struct.unpack_from("<f", raw, OFF_ROT)[0]
    skew = struct.unpack_from("<f", raw, OFF_SKEW)[0]
    color = list(raw[OFF_COLOR:OFF_COLOR + 4])
    mask = bool(raw[OFF_MASK])
    shape_word = struct.unpack_from("<H", raw, OFF_SHAPE)[0]
    return {
        "type": TYPE_CODE_BASE + int(shape_word),
        "data": [
            _safe_float(x), _safe_float(y), _safe_float(sx), _safe_float(sy),
            _safe_float(rotation), _safe_float(skew), 1 if mask else 0,
        ],
        "color": color,
        "score": 0,
    }


def _iter_signature_candidates(handle: int, base: int, size: int):
    """在固定偏移与整个主模块镜像中查找彩绘签名，返回所有命中地址。"""
    seen: set[int] = set()
    fixed_addr = base + SIG_SCAN_START
    fixed_size = min(SIG_SCAN_SIZE, max(0, size - SIG_SCAN_START))
    if fixed_size > 0:
        raw = _read(handle, fixed_addr, fixed_size)
        offset = raw.find(SIGNATURE)
        if offset >= 0:
            yield fixed_addr + offset

    pos = base
    end = base + size
    while pos < end:
        n = min(CHUNK_SIZE, end - pos)
        raw = _read(handle, pos, n)
        start = 0
        while raw:
            offset = raw.find(SIGNATURE, start)
            if offset < 0:
                break
            addr = pos + offset
            if addr not in seen:
                seen.add(addr)
                yield addr
            start = offset + 1
        pos += n


def _resolve_signature_candidate(handle: int, pre: int) -> Tuple[int, int, int]:
    """从签名地址出发走 FH5 风格的指针链，校验并返回 group/count/table。"""
    addr_a = _read_u64(handle, pre + OFF_ROOT)
    if not _is_plausible_ptr(addr_a):
        raise Fh6DumpError("彩绘指针链无效（根指针）。")
    addr_b = _read_u64(handle, addr_a + OFF_EDITOR)
    if not _is_plausible_ptr(addr_b):
        raise Fh6DumpError("彩绘指针链无效（编辑器指针）。")
    c_livery = _read_u64(handle, addr_b + OFF_LIVERY)
    if not _is_plausible_ptr(c_livery):
        raise Fh6DumpError("彩绘指针链无效（彩绘指针）。")
    group = _read_u64(handle, c_livery + OFF_GROUP)
    if not _is_plausible_ptr(group):
        raise Fh6DumpError("彩绘指针链无效（彩绘组）。")
    count = _read_u16(handle, group + OFF_COUNT)
    if not (1 <= count <= MAX_COUNT):
        raise Fh6DumpError(f"彩绘组图层数异常（{count}），请确认已在游戏里打开一个彩绘组。")
    table = _read_u64(handle, group + OFF_TABLE)
    if not _is_plausible_ptr(table):
        raise Fh6DumpError("彩绘组图层表指针无效。")
    sample = min(count, 8)
    ptrs_raw = _read(handle, table, sample * 8)
    if len(ptrs_raw) < sample * 8:
        raise Fh6DumpError("彩绘组图层表无法读取。")
    valid = sum(
        1 for j in range(sample)
        if _is_plausible_ptr(struct.unpack_from("<Q", ptrs_raw, j * 8)[0])
    )
    if valid < min(sample, 1):
        raise Fh6DumpError("彩绘组图层表指针异常。")
    return group, count, table


def _locate_by_signature(handle: int) -> Tuple[int, int, int]:
    base, size = _module_info(handle)
    if not base:
        raise Fh6DumpError("游戏主模块基址无效。")
    last_error: Optional[str] = None
    for pre in _iter_signature_candidates(handle, base, size):
        try:
            return _resolve_signature_candidate(handle, pre)
        except Fh6DumpError as exc:
            last_error = str(exc)
    if last_error:
        raise Fh6DumpError(last_error)
    raise Fh6DumpError("未在内存中找到彩绘签名。")


def _iter_regions(handle: int):
    addr = 0x10000
    max_addr = 0x7FFFFFFFFFFF
    info = MBI()
    while addr < max_addr:
        if not kernel32.VirtualQueryEx(handle, addr, ctypes.byref(info), ctypes.sizeof(info)):
            addr += 0x10000
            continue
        base = int(info.BaseAddress)
        size = int(info.RegionSize)
        protect = int(info.Protect)
        state = int(info.State)
        typ = int(info.Type)
        rw = not (protect & PAGE_GUARD or protect & PAGE_NOACCESS) and bool(protect & RW_MASK)
        if state == MEM_COMMIT and typ == MEM_PRIVATE and rw:
            yield base, base + size
        nxt = base + size
        if nxt <= addr:
            break
        addr = nxt


def _build_contains(regions):
    ranges = sorted((base, end) for base, end in regions)

    def contains(value):
        value = int(value)
        if not _is_plausible_ptr(value):
            return False
        lo, hi = 0, len(ranges) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            start, stop = ranges[mid]
            if value < start:
                hi = mid - 1
            elif value >= stop:
                lo = mid + 1
            else:
                return True
        return False

    return contains


def _locate_by_scan(handle: int, deadline: float, cancel_event=None) -> Tuple[int, int, int]:
    best_score = -1
    best = (0, 0, 0)
    unpack_u16 = struct.unpack_from
    unpack_u64 = struct.unpack_from
    regions = list(_iter_regions(handle))
    if not regions:
        raise Fh6DumpError("未能枚举游戏内存区域。")
    contains = _build_contains(regions)
    regions.sort(key=lambda r: r[1] - r[0], reverse=True)
    checked = 0
    iterations = 0
    for base, end in regions:
        region_size = end - base
        if region_size < 0x100:
            continue
        pos = base
        while pos < end:
            if time.monotonic() > deadline:
                raise Fh6DumpError(
                    "内存扫描超时：未能快速定位当前彩绘组。请确认已在游戏内打开一个彩绘组，并重试。"
                )
            if cancel_event is not None and cancel_event.is_set():
                raise Fh6DumpError("已取消。")
            n = min(CHUNK_SIZE, end - pos)
            raw = _read(handle, pos, n)
            if raw:
                for i in range(0, len(raw) - 0x90, 4):
                    iterations += 1
                    if iterations % 262144 == 0:
                        if time.monotonic() > deadline:
                            raise Fh6DumpError(
                                "内存扫描超时：未能快速定位当前彩绘组。请确认已在游戏内打开一个彩绘组，并重试。"
                            )
                        time.sleep(0.001)
                    count = unpack_u16("<H", raw, i + OFF_COUNT)[0]
                    if not (1 <= count <= MAX_COUNT):
                        continue
                    table = unpack_u64("<Q", raw, i + OFF_TABLE)[0]
                    table_end = unpack_u64("<Q", raw, i + OFF_TABLE_END)[0]
                    table_cap = unpack_u64("<Q", raw, i + OFF_TABLE_CAPACITY)[0]
                    if not (_is_plausible_ptr(table) and _is_plausible_ptr(table_end) and _is_plausible_ptr(table_cap)):
                        continue
                    if table_end != table + count * 8 or table_cap < table_end:
                        continue
                    if not (contains(table) and contains(table_end - 1) and contains(table_cap - 1)):
                        continue
                    capacity_count = (table_cap - table) // 8
                    if capacity_count < count or capacity_count > max(count + 10000, count * 16):
                        continue
                    group = pos + i
                    if not contains(group):
                        continue
                    sample = min(count, 64)
                    ptrs_raw = _read(handle, table, sample * 8)
                    if len(ptrs_raw) < sample * 8:
                        continue
                    valid = 0
                    for j in range(sample):
                        if contains(unpack_u64("<Q", ptrs_raw, j * 8)[0]):
                            valid += 1
                    if valid < min(sample, max(1, count // 4)):
                        continue
                    score = valid * 10000 + count
                    if score > best_score:
                        best_score = score
                        best = (group, count, table)
                    checked += 1
                # 周期性让出 GIL，避免纯 Python 扫描卡住界面
                time.sleep(0.001)
            pos += n
    if best_score < 0:
        raise Fh6DumpError("未能定位彩绘组，请确认已在游戏里打开一个彩绘组。")
    return best


def locate_group(handle: int, deadline: float) -> Tuple[int, int, int]:
    try:
        return _locate_by_signature(handle)
    except Fh6DumpError:
        return _locate_by_scan(handle, deadline)


def _validate_group(handle: int, group: int, count: int, contains) -> Optional[int]:
    """校验候选 group 头，返回图层表指针；不合法返回 None。"""
    if not contains(group):
        return None
    table = _read_u64(handle, group + OFF_TABLE)
    table_end = _read_u64(handle, group + OFF_TABLE_END)
    table_cap = _read_u64(handle, group + OFF_TABLE_CAPACITY)
    if not (_is_plausible_ptr(table) and _is_plausible_ptr(table_end) and _is_plausible_ptr(table_cap)):
        return None
    if table_end != table + count * 8 or table_cap < table_end:
        return None
    if not (contains(table) and contains(table_end - 1) and contains(table_cap - 1)):
        return None
    capacity_count = (table_cap - table) // 8
    if capacity_count < count or capacity_count > max(count + 10000, count * 16):
        return None
    sample = min(count, 8)
    ptrs_raw = _read(handle, table, sample * 8)
    if len(ptrs_raw) < sample * 8:
        return None
    valid = sum(
        1 for j in range(sample)
        if contains(struct.unpack_from("<Q", ptrs_raw, j * 8)[0])
    )
    if valid < min(sample, max(1, count // 4)):
        return None
    return table


def locate_table_by_count(handle: int, count: int, deadline: float, on_progress=None, cancel_event=None) -> Tuple[int, int]:
    """按图层数量快速定位：搜索 count 的小端 u16 字节模式并按 vtable+图层解码校验。"""
    count = int(count)
    if not (1 <= count <= MAX_COUNT):
        raise Fh6DumpError(f"图层数量无效：{count}（应在 1~{MAX_COUNT} 之间）。")
    regions = list(_iter_regions(handle))
    if not regions:
        raise Fh6DumpError("未能枚举游戏内存区域。")
    contains = _build_contains(regions)
    regions.sort(key=lambda r: r[1] - r[0], reverse=True)
    mod_base, mod_size = _module_info(handle)
    mod_end = mod_base + mod_size
    pattern = struct.pack("<H", count)
    region_count = len(regions)
    region_index = 0

    for base, end in regions:
        region_index += 1
        if on_progress and region_index % 100 == 0:
            on_progress(f"正在扫描内存区域 {region_index}/{region_count}…")
        if end - base < 0x100:
            continue
        pos = base
        while pos < end:
            if time.monotonic() > deadline:
                raise Fh6DumpError("按图层数量定位超时，请确认图层数量正确后重试。")
            if cancel_event is not None and cancel_event.is_set():
                raise Fh6DumpError("已取消。")
            n = min(CHUNK_SIZE, end - pos)
            raw = _read(handle, pos, n)
            start = 0
            while raw:
                offset = raw.find(pattern, start)
                if offset < 0:
                    break
                goff = offset - OFF_COUNT
                if 0 <= goff < len(raw) - 0x90:
                    vtable = struct.unpack_from("<Q", raw, goff)[0]
                    if mod_base <= vtable < mod_end:
                        group = pos + goff
                        table = struct.unpack_from("<Q", raw, goff + OFF_TABLE)[0]
                        if not (_is_plausible_ptr(table) and contains(table)):
                            start = offset + 1
                            continue
                        sample = min(count, 16)
                        ok_layers = 0
                        for j in range(sample):
                            lp = _read_u64(handle, table + j * 8)
                            if not (_is_plausible_ptr(lp) and contains(lp)):
                                continue
                            layer_raw = _read(handle, lp, LAYER_SIZE)
                            if len(layer_raw) != LAYER_SIZE:
                                layer_raw = _read(handle, lp, LAYER_SAFE_SIZE)
                            if layer_plausible(layer_raw):
                                ok_layers += 1
                        if ok_layers >= max(1, sample // 2):
                            return group, table
                start = offset + 1
            pos += n
            time.sleep(0.001)
    raise Fh6DumpError(
        f"未找到图层数量为 {count} 的有效彩绘组。请确认数量正确、彩绘组已在游戏内打开并完全展开。"
    )


def locate_table_by_vtables(handle: int, vtables, deadline: float, on_progress=None, cancel_event=None) -> Tuple[int, int, int]:
    """按已知 vtable 快速扫描对象（首 8 字节 = vtable）并读取组结构。"""
    if not vtables:
        raise Fh6DumpError("未提供可用于定位的 vtable。")
    regions = list(_iter_regions(handle))
    if not regions:
        raise Fh6DumpError("未能枚举游戏内存区域。")
    contains = _build_contains(regions)
    regions.sort(key=lambda r: r[1] - r[0], reverse=True)
    patterns = [struct.pack("<Q", int(v)) for v in vtables]
    region_count = len(regions)
    region_index = 0
    for base, end in regions:
        region_index += 1
        if on_progress and region_index % 100 == 0:
            on_progress(f"正在扫描内存区域 {region_index}/{region_count}…")
        if end - base < 0x100:
            continue
        pos = base
        while pos < end:
            if time.monotonic() > deadline:
                raise Fh6DumpError("按 vtable 定位超时。")
            if cancel_event is not None and cancel_event.is_set():
                raise Fh6DumpError("已取消。")
            n = min(CHUNK_SIZE, end - pos)
            raw = _read(handle, pos, n)
            for pattern in patterns:
                start = 0
                while raw:
                    offset = raw.find(pattern, start)
                    if offset < 0:
                        break
                    group = pos + offset
                    count = struct.unpack_from("<H", raw, offset + OFF_COUNT)[0]
                    if 1 <= count <= MAX_COUNT:
                        table = struct.unpack_from("<Q", raw, offset + OFF_TABLE)[0]
                        if _is_plausible_ptr(table) and contains(table):
                            return group, count, table
                    start = offset + 1
            pos += n
            time.sleep(0.001)
    raise Fh6DumpError("按 vtable 未找到有效彩绘组。")


def dump_fh6(
    pid: Optional[int] = None,
    timeout: float = DEFAULT_SCAN_TIMEOUT,
    count: Optional[int] = None,
    on_progress=None,
    cancel_event=None,
) -> Dict[str, Any]:
    def progress(message: str) -> None:
        if on_progress is not None:
            try:
                on_progress(message)
            except Exception:
                pass

    pid = int(pid) if pid else _find_pid()
    progress(f"已找到 ForzaHorizon6 进程（PID {pid}）。")
    handle = _open_process(pid)
    progress("已打开进程，正在定位当前彩绘组…")
    shapes: List[Dict[str, Any]] = []
    deadline = time.monotonic() + max(1.0, float(timeout))
    try:
        if cancel_event is not None and cancel_event.is_set():
            raise Fh6DumpError("已取消。")
        if count is not None:
            progress(f"正在按图层数量 {int(count)} 快速定位…")
            _group, table = locate_table_by_count(handle, int(count), deadline, progress, cancel_event)
            layer_count = int(count)
        else:
            progress("正在按已知 vtable 定位彩绘组…")
            mod_base, _mod_size = _module_info(handle)
            vtable_va = mod_base + GROUP_VTABLE_RVA
            try:
                _group, layer_count, table = locate_table_by_vtables(handle, [vtable_va], deadline, progress, cancel_event)
            except Fh6DumpError:
                progress("vtable 定位未命中，正在通过签名/内存扫描…")
                try:
                    _group, layer_count, table = _locate_by_signature(handle)
                except Fh6DumpError:
                    _group, layer_count, table = _locate_by_scan(handle, deadline, cancel_event)
        progress(f"已定位彩绘组（共 {layer_count} 个图层），正在读取…")
        for index in range(layer_count):
            if time.monotonic() > deadline:
                raise Fh6DumpError("读取图层超时，请确认彩绘组完整展开后重试。")
            if cancel_event is not None and cancel_event.is_set():
                raise Fh6DumpError("已取消。")
            ptr = _read_u64(handle, table + index * 8)
            if not _is_plausible_ptr(ptr):
                continue
            raw = _read(handle, ptr, LAYER_SIZE)
            if len(raw) != LAYER_SIZE:
                raw = _read(handle, ptr, LAYER_SAFE_SIZE)
            shape = decode_layer(raw)
            if shape is not None:
                shapes.append(shape)
        if not shapes:
            raise Fh6DumpError("彩绘组中没有可读取的图层。")
        progress(f"已读取 {len(shapes)} 个图层。")
    finally:
        kernel32.CloseHandle(handle)
    return {
        "format": "fh6_native_dump_v1",
        "game": "fh6",
        "pid": pid,
        "layer_count": len(shapes),
        "shapes": shapes,
    }
