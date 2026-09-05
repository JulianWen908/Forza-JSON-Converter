# -*- coding: utf-8 -*-
"""
Forza Horizon 5 / Forza Horizon 6 vinyl JSON 格式转换核心模块。

格式说明（已通过 FH5 ForzaPainter 与 FH6 Vinylizer 实际文件交叉验证）：

FH5（forza-painter.exe 导出，原生格式）:
    {"shapes":
    [{"type":1, "data":[0,0,W,H],"color":[255,0,255,0],"score":0},   <- 画布描述元素
    {"type":16, "data":[x,y,w,h,rot],"color":[r,g,b,a],"score":...},
    ...
    ]}
    * 每个形状一行；data 全部为整数像素坐标；行尾 CRLF。

FH6（Vinylizer 导出）:
    {"shapes": [
        {"type": 1,   "data": [x,y,w,h,rot], "color": [r,g,b,a], "score": 0},  # 矩形
        {"type": 16,  "data": [x,y,w,h,rot], "color": [r,g,b,a], "score": 0},  # 椭圆
        {"type": 103, "data": [x,y,w,h,rot], "color": [r,g,b,a], "score": 0},  # 三角形
        {"type": 228, "data": [x,y,w,h,rot], "color": [r,g,b,a], "score": 0},  # 软边椭圆
        ...
    ]}

本模块不依赖任何第三方库，纯标准库实现。
"""

from __future__ import annotations

import json
import math
import os
from typing import Any, Dict, List, Optional, Tuple

import i18n

# ---------------------------------------------------------------------------
# 类型码定义
# ---------------------------------------------------------------------------

FH6_RECT = 1            # 矩形（游戏内存 shape_id 101）
FH6_ELLIPSE = 16        # 椭圆（游戏内存 shape_id 102）
FH6_TRIANGLE = 103      # 三角形（游戏内存 shape_id 103 = 0x67）
FH6_SOFT_ELLIPSE = 228  # 软边椭圆（游戏内存 shape_id 228 = 0xE4）

# FH5 完整类型码（0x100000 + shape word），来自用户提供的映射表
FH5_RECT = 1048677          # 矩形/正方形（shape word 101）
FH5_ELLIPSE = 1048678       # 硬边椭圆/圆（shape word 102）
FH5_TRIANGLE = 1048679      # 等边三角形（shape word 103）
FH5_SOFT_ELLIPSE = 1048804  # 全软椭圆（shape word 228）

FH5_TYPE_MAP = {
    FH6_RECT: FH5_RECT,
    FH6_ELLIPSE: FH5_ELLIPSE,
    FH6_TRIANGLE: FH5_TRIANGLE,
    FH6_SOFT_ELLIPSE: FH5_SOFT_ELLIPSE,
}
FH6_TYPE_MAP = {value: key for key, value in FH5_TYPE_MAP.items()}
FH5_FULL_CODES = frozenset(FH5_TYPE_MAP.values())

# 新旧几何格式通用的类型别名（FH5 工具沿用的 legacy 格式）
LEGACY_RECT_TYPES = (1, 2)      # 1=普通矩形 2=旋转矩形
LEGACY_ELLIPSE_TYPES = (8, 16)  # 8=普通椭圆 16=旋转椭圆

KNOWN_FH6_TYPES = frozenset({FH6_RECT, FH6_ELLIPSE, FH6_TRIANGLE, FH6_SOFT_ELLIPSE})

# FH5 画布描述元素使用的颜色（品红色，alpha=0）
FH5_CANVAS_COLOR = [255, 0, 255, 0]

# 警告项：code + 参数
Warning = Tuple[str, Dict[str, Any]]


class FormatError(ValueError):
    """文件格式无法识别或解析失败时抛出。code 用于多语言渲染。"""

    def __init__(self, code: str, params: Optional[Dict[str, Any]] = None) -> None:
        self.code = code
        self.params = params or {}
        super().__init__(i18n.get(code, **self.params))


class DetectionResult:
    def __init__(
        self,
        format_name: str,            # "fh5" / "fh6" / "unknown"
        shape_count: int,
        canvas: Optional[Dict[str, Any]],
        type_counts: Dict[int, int],
        warnings: List[Warning],
    ) -> None:
        self.format_name = format_name
        self.shape_count = shape_count
        self.canvas = canvas
        self.type_counts = type_counts
        self.warnings = warnings

    def type_summary(self) -> str:
        if not self.type_counts:
            return "—"
        return ", ".join(f"type {key}: {count}" for key, count in sorted(self.type_counts.items()))


class ConversionResult:
    def __init__(
        self,
        payload: Dict[str, Any],
        source_format: str,
        target_format: str,
        shape_count: int,
        warnings: List[Warning],
    ) -> None:
        self.payload = payload
        self.source_format = source_format
        self.target_format = target_format
        self.shape_count = shape_count
        self.warnings = warnings


# ---------------------------------------------------------------------------
# 基础工具函数
# ---------------------------------------------------------------------------

def to_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if isinstance(value, str):
        text = value.strip()
        try:
            return int(text, 0)
        except ValueError:
            return None
    return None


def to_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_canvas_sentinel(shape: Dict[str, Any]) -> bool:
    """判断是否为 FH5 画布描述元素：type=1、data 恰好 4 个值、坐标为 [0, 0, W, H]、alpha<=0。"""
    if to_int(shape.get("type")) != 1:
        return False
    data = shape.get("data")
    if not isinstance(data, (list, tuple)) or len(data) != 4:
        return False
    try:
        x, y, w, h = [float(v) for v in data]
    except (TypeError, ValueError):
        return False
    if x != 0.0 or y != 0.0 or w <= 0 or h <= 0:
        return False
    color = shape.get("color")
    if isinstance(color, (list, tuple)) and len(color) >= 4:
        try:
            if float(color[3]) > 0:
                return False
        except (TypeError, ValueError):
            pass
    return True


def extract_shapes(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        raise FormatError("err.top_level")
    for key in ("shapes", "Shapes"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    raise FormatError("err.no_shapes_key")


def load_json(path: str) -> Any:
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise FormatError("err.json_parse", {"line": exc.lineno, "col": exc.colno, "msg": exc.msg}) from exc
    except OSError as exc:
        raise FormatError("err.file_read", {"err": exc}) from exc


def _fmt_number(value: Any) -> str:
    """按 forza-painter 原生风格输出数字：整数不带小数点。"""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return repr(value)
    return str(value)


def dump_fh6_json(path: str, payload: Dict[str, Any]) -> None:
    """FH6 输出：与 Vinylizer 自身输出一致（2 空格缩进）。"""
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def dump_fh5_json(path: str, payload: Dict[str, Any]) -> None:
    """
    FH5 输出：与 forza-painter.exe 原生格式逐字节一致——
      * 首行 {"shapes":
      * 每个形状一行（紧凑 JSON）
      * CRLF 行尾
      * 末行 ]}
    """
    shapes = payload.get("shapes", [])
    shape_lines = []
    for shape in shapes:
        data = shape.get("data", [])
        color = shape.get("color", [])
        score = shape.get("score", 0)
        line = (
            '{"type":%s, "data":[%s],"color":[%s],"score":%s}'
            % (
                _fmt_number(shape.get("type")),
                ",".join(_fmt_number(v) for v in data),
                ",".join(_fmt_number(v) for v in color),
                _fmt_number(score),
            )
        )
        shape_lines.append(line)

    body = ",\r\n".join(shape_lines)
    text = '{"shapes":\r\n[' + body + "\r\n]}"

    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="ascii", newline="") as handle:
        handle.write(text)


# ---------------------------------------------------------------------------
# 格式识别
# ---------------------------------------------------------------------------

def detect_format(payload: Any) -> DetectionResult:
    warnings: List[Warning] = []
    shapes = extract_shapes(payload)
    if not shapes:
        raise FormatError("err.empty_shapes")

    # FH6 内存导出（原生格式：完整类型码 + 内存坐标）
    if isinstance(payload, dict) and payload.get("format") == "fh6_native_dump_v1":
        type_counts: Dict[int, int] = {}
        for shape in shapes:
            if not isinstance(shape, dict):
                continue
            type_id = to_int(shape.get("type"))
            if type_id is not None:
                type_counts[type_id] = type_counts.get(type_id, 0) + 1
        return DetectionResult("fh6_native", len(shapes), None, type_counts, warnings)

    type_counts: Dict[int, int] = {}
    data_len_counts: Dict[int, int] = {}
    has_canvas = False
    for index, shape in enumerate(shapes):
        if not isinstance(shape, dict):
            warnings.append(("warn.shape_skipped", {"index": index + 1}))
            continue
        type_id = to_int(shape.get("type"))
        if type_id is not None:
            type_counts[type_id] = type_counts.get(type_id, 0) + 1
        data = shape.get("data")
        if isinstance(data, (list, tuple)):
            data_len_counts[len(data)] = data_len_counts.get(len(data), 0) + 1
        if index == 0 and is_canvas_sentinel(shape):
            has_canvas = True

    if not type_counts:
        raise FormatError("err.no_valid_type")

    unknown_types = sorted(t for t in type_counts if t not in KNOWN_FH6_TYPES and t not in FH5_FULL_CODES)
    if unknown_types:
        warnings.append(("warn.unknown_types", {"types": ", ".join(str(t) for t in unknown_types)}))

    if has_canvas:
        warnings.append(("warn.canvas_found", {}))
        return DetectionResult("fh5", len(shapes), shapes[0], type_counts, warnings)

    if len(shapes) == 1 and 1 in type_counts and data_len_counts.get(4, 0) == 1:
        warnings.append(("warn.only_canvas", {}))
        return DetectionResult("unknown", len(shapes), None, type_counts, warnings)

    if set(type_counts) <= FH5_FULL_CODES:
        return DetectionResult("fh5", len(shapes), None, type_counts, warnings)

    if set(type_counts) <= KNOWN_FH6_TYPES:
        if 103 in type_counts or 228 in type_counts:
            return DetectionResult("fh6", len(shapes), None, type_counts, warnings)
        if data_len_counts.get(4, 0):
            warnings.append(("warn.rect4", {}))
        return DetectionResult("fh6", len(shapes), None, type_counts, warnings)

    if unknown_types:
        warnings.append(("warn.unknown_without_canvas", {}))
        return DetectionResult("unknown", len(shapes), None, type_counts, warnings)

    warnings.append(("warn.ambiguous", {}))
    return DetectionResult("unknown", len(shapes), None, type_counts, warnings)


# ---------------------------------------------------------------------------
# 形状归一化
# ---------------------------------------------------------------------------

def normalize_shape(shape: Dict[str, Any], index: int, warnings: List[Warning]) -> Optional[Dict[str, Any]]:
    if not isinstance(shape, dict):
        warnings.append(("warn.shape_skipped", {"index": index + 1}))
        return None

    type_id = to_int(shape.get("type"))
    if type_id is None:
        warnings.append(("warn.shape_skipped", {"index": index + 1}))
        return None

    data = shape.get("data")
    if not isinstance(data, (list, tuple)) or not data:
        warnings.append(("warn.shape_skipped", {"index": index + 1}))
        return None

    numbers: List[float] = []
    bad = False
    for value in data:
        num = to_float(value)
        if num is None:
            bad = True
            break
        numbers.append(num)
    if bad or len(numbers) < 4:
        warnings.append(("warn.shape_skipped", {"index": index + 1}))
        return None

    color = shape.get("color")
    color_values: List[int] = []
    if isinstance(color, (list, tuple)) and len(color) >= 3:
        for value in color[:4]:
            num = to_float(value)
            if num is None:
                color_values = []
                break
            color_values.append(max(0, min(255, int(round(num)))))
        if len(color) == 3 and color_values:
            color_values.append(255)
    if len(color_values) < 3:
        warnings.append(("warn.shape_skipped", {"index": index + 1}))
        return None

    score = shape.get("score", 0.0)
    score_num = to_float(score)

    return {
        "type": type_id,
        "data": numbers,
        "color": color_values,
        "score": score_num if score_num is not None else 0.0,
    }


# ---------------------------------------------------------------------------
# 转换主逻辑
# ---------------------------------------------------------------------------

TRIANGLE_NORMAL_FACTOR = 0.59  # “正常的三角形”对应的比例（59%）


def scale_divisor(type_id: int, triangle_scale: float = 0.59) -> float:
    """
    形状的基础尺寸除数：
      矩形为 127；椭圆/软边椭圆为 63；
      三角形以 59%（“正常”）为锚点：59% 对应除数 63/0.59，
      其余比例按线性缩放（比例越大，除数越大，三角形越小）。
    """
    if type_id in LEGACY_RECT_TYPES or type_id == FH5_RECT:
        return 127.0
    if type_id in (FH6_TRIANGLE, FH5_TRIANGLE):
        factor = max(0.05, min(2.0, float(triangle_scale)))
        anchor = 63.0 / TRIANGLE_NORMAL_FACTOR
        return anchor * (factor / TRIANGLE_NORMAL_FACTOR)
    return 63.0


def pixel_to_memory(data: List[Any], divisor: float) -> List[float]:
    """把像素坐标 [x, y, w, h, rot] 转成游戏内存坐标 [x, -y, w/div, h/div, 360-rot, skew, mask]。"""
    x = float(data[0])
    y = float(data[1])
    w = float(data[2])
    h = float(data[3])
    rot = float(data[4]) if len(data) >= 5 else 0.0
    return [x, -y, w / divisor, h / divisor, (360.0 - rot) % 360.0, 0.0, 0.0]


def memory_to_pixel(data: List[Any], divisor: float) -> List[float]:
    """把游戏内存坐标转回像素坐标（pixel_to_memory 的逆运算）。"""
    x = float(data[0])
    y = float(data[1])
    sx = float(data[2])
    sy = float(data[3])
    rot = float(data[4]) if len(data) >= 5 else 0.0
    return [x, -y, sx * divisor, sy * divisor, (360.0 - rot) % 360.0]


def native_canvas_divisor(type_id: int) -> float:
    """从内存坐标估算画布尺寸用的基础尺寸：矩形 127，其余 63。"""
    if type_id == FH5_RECT or type_id in LEGACY_RECT_TYPES:
        return 127.0
    return 63.0


def fh5_to_fh6(payload: Any, triangle_scale: float = 0.59) -> ConversionResult:
    warnings: List[Warning] = []
    shapes = extract_shapes(payload)
    if not shapes:
        raise FormatError("err.empty_shapes")

    out_shapes: List[Dict[str, Any]] = []
    removed_canvas = False

    for index, shape in enumerate(shapes):
        if index == 0 and is_canvas_sentinel(shape):
            removed_canvas = True
            continue
        normalized = normalize_shape(shape, index, warnings)
        if normalized is None:
            continue

        type_id = normalized["type"]
        new_type = type_id
        is_full_code = type_id in FH5_FULL_CODES
        if is_full_code:
            new_type = FH6_TYPE_MAP.get(type_id, type_id)
        elif type_id in LEGACY_RECT_TYPES:
            new_type = FH6_RECT
        elif type_id in LEGACY_ELLIPSE_TYPES:
            new_type = FH6_ELLIPSE
        elif type_id in KNOWN_FH6_TYPES:
            new_type = type_id
        else:
            warnings.append(("warn.shape_unknown", {"index": index + 1, "type": type_id}))
        normalized["type"] = new_type

        if is_full_code:
            # 完整类型码用的是游戏内存坐标，反向转回像素坐标
            normalized["data"] = memory_to_pixel(normalized["data"], scale_divisor(type_id, triangle_scale))

        if len(normalized["data"]) == 4:
            normalized["data"] = normalized["data"] + [0.0]
        out_shapes.append(normalized)

    if removed_canvas:
        warnings.append(("warn.canvas_removed", {}))
    else:
        warnings.append(("warn.no_canvas_found", {}))

    return ConversionResult(
        payload={"shapes": out_shapes},
        source_format="fh5",
        target_format="fh6",
        shape_count=len(out_shapes),
        warnings=warnings,
    )


def infer_canvas_size(shapes: List[Dict[str, Any]]) -> Tuple[int, int]:
    max_x = 0.0
    max_y = 0.0
    any_shape = False
    for shape in shapes:
        data = shape.get("data")
        if not isinstance(data, (list, tuple)) or len(data) < 4:
            continue
        try:
            x, y, w, h = [abs(float(v)) for v in data[:4]]
        except (TypeError, ValueError):
            continue
        max_x = max(max_x, x + w)
        max_y = max(max_y, y + h)
        any_shape = True
    if not any_shape:
        raise FormatError("err.canvas_infer")
    return max(1, int(math.ceil(max_x))), max(1, int(math.ceil(max_y)))


def fh6_to_fh5(payload: Any, triangle_scale: float = 0.59) -> ConversionResult:
    """
    FH6 -> FH5：
      * 在开头加入 FH5 画布描述元素
      * 按映射表转换形状类型为 FH5 完整类型码：
        矩形1→1048677、椭圆16→1048678、三角形103→1048679、软边椭圆228→1048804
      * 像素坐标转换为游戏内存坐标：x、-y、宽高除以基础尺寸（矩形127/其余63）、旋转角取反
    """
    warnings: List[Warning] = []
    shapes = extract_shapes(payload)
    if not shapes:
        raise FormatError("err.empty_shapes")

    out_shapes: List[Dict[str, Any]] = []
    max_x = 0.0
    max_y = 0.0
    has_pixel_extent = False

    for index, shape in enumerate(shapes):
        if index == 0 and is_canvas_sentinel(shape):
            warnings.append(("warn.input_canvas_skipped", {}))
            continue
        normalized = normalize_shape(shape, index, warnings)
        if normalized is None:
            continue

        type_id = normalized["type"]
        # 映射为 FH5 完整类型码
        if type_id in LEGACY_RECT_TYPES:
            new_type = FH5_RECT
        elif type_id in LEGACY_ELLIPSE_TYPES:
            new_type = FH5_ELLIPSE
        elif type_id in KNOWN_FH6_TYPES:
            new_type = FH5_TYPE_MAP.get(type_id, type_id)
        elif type_id in FH5_FULL_CODES:
            new_type = type_id
        else:
            new_type = type_id
            warnings.append(("warn.shape_unknown", {"index": index + 1, "type": type_id}))
        normalized["type"] = new_type

        # 用像素坐标计算画布外接范围（转换前）
        data = normalized["data"]
        if len(data) >= 4:
            max_x = max(max_x, abs(float(data[0])) + abs(float(data[2])))
            max_y = max(max_y, abs(float(data[1])) + abs(float(data[3])))
            has_pixel_extent = True

        # 像素坐标 -> 游戏内存坐标
        normalized["data"] = pixel_to_memory(data, scale_divisor(type_id, triangle_scale))
        out_shapes.append(normalized)

    if not out_shapes:
        raise FormatError("err.no_drawables")
    if not has_pixel_extent:
        raise FormatError("err.canvas_infer")

    warnings.append(("warn.types_mapped", {}))

    width = max(1, int(math.ceil(max_x)))
    height = max(1, int(math.ceil(max_y)))
    canvas = {
        "type": 1,
        "data": [0, 0, width, height],
        "color": list(FH5_CANVAS_COLOR),
        "score": 0.0,
    }
    warnings.append(("warn.canvas_added", {"width": width, "height": height}))
    warnings.append(("warn.coords_to_memory", {}))

    return ConversionResult(
        payload={"shapes": [canvas] + out_shapes},
        source_format="fh6",
        target_format="fh5",
        shape_count=len(out_shapes),
        warnings=warnings,
    )


def native_fh6_to_fh5(payload: Any) -> ConversionResult:
    """
    FH6 原生（内存导出）-> FH5：
      输入已是 FH5 内存坐标（完整类型码 + [x,y,sx,sy,rot,skew,mask]），
      仅需在最前插入画布元素，形状 data 原样保留。
    """
    warnings: List[Warning] = []
    shapes = extract_shapes(payload)
    if not shapes:
        raise FormatError("err.empty_shapes")

    out_shapes: List[Dict[str, Any]] = []
    max_x = 0.0
    max_y = 0.0
    has_extent = False

    for index, shape in enumerate(shapes):
        if index == 0 and is_canvas_sentinel(shape):
            warnings.append(("warn.input_canvas_skipped", {}))
            continue
        normalized = normalize_shape(shape, index, warnings)
        if normalized is None:
            continue

        type_id = normalized["type"]
        data = normalized["data"]
        if len(data) >= 4:
            pixel = memory_to_pixel(data, native_canvas_divisor(type_id))
            max_x = max(max_x, abs(pixel[0]) + abs(pixel[2]))
            max_y = max(max_y, abs(pixel[1]) + abs(pixel[3]))
            has_extent = True
        out_shapes.append(normalized)

    if not out_shapes:
        raise FormatError("err.no_drawables")
    if not has_extent:
        raise FormatError("err.canvas_infer")

    width = max(1, int(math.ceil(max_x)))
    height = max(1, int(math.ceil(max_y)))
    canvas = {
        "type": 1,
        "data": [0, 0, width, height],
        "color": list(FH5_CANVAS_COLOR),
        "score": 0.0,
    }
    warnings.append(("warn.canvas_added", {"width": width, "height": height}))

    return ConversionResult(
        payload={"shapes": [canvas] + out_shapes},
        source_format="fh6",
        target_format="fh5",
        shape_count=len(out_shapes),
        warnings=warnings,
    )


def convert_payload(payload: Any, direction: str, triangle_scale: float = 0.59) -> ConversionResult:
    if direction == "fh5_to_fh6":
        return fh5_to_fh6(payload, triangle_scale)
    if direction == "fh6_to_fh5":
        return fh6_to_fh5(payload, triangle_scale)
    if direction == "fh6_native_to_fh5":
        return native_fh6_to_fh5(payload)
    raise FormatError("err.bad_direction", {"direction": direction})


def render_warning(warning: Warning, lang: Optional[str] = None) -> str:
    """把结构化警告渲染成指定语言（默认 i18n 当前语言）的文本。"""
    code, params = warning
    if lang:
        return i18n.get_in(code, lang, **params)
    return i18n.get(code, **params)


def render_warnings(warnings: List[Warning], lang: Optional[str] = None) -> List[str]:
    return [render_warning(w, lang) for w in warnings]


def convert_file(source_path: str, target_path: str, direction: str, triangle_scale: float = 0.59) -> ConversionResult:
    """读取文件、转换、按目标格式写出。"""
    payload = load_json(source_path)
    result = convert_payload(payload, direction, triangle_scale)
    if direction == "fh5_to_fh6":
        dump_fh6_json(target_path, result.payload)
    else:
        dump_fh5_json(target_path, result.payload)
    return result
