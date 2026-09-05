# -*- coding: utf-8 -*-
"""转换核心模块的自动化测试。"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import converter_core as core


FH5_SAMPLE = r"C:/Users/wjunj/Desktop/Forza Painter Master/forza-painter-master/ASU fh5.json"
FH6_SAMPLE = r"E:/Vinylizer Files/asu v1 1850.json"


class TestDetection(unittest.TestCase):
    def test_detect_fh5(self):
        payload = core.load_json(FH5_SAMPLE)
        result = core.detect_format(payload)
        self.assertEqual(result.format_name, "fh5")
        self.assertEqual(result.shape_count, 2300)
        self.assertIsNotNone(result.canvas)
        self.assertIn(16, result.type_counts)
        self.assertEqual(result.type_counts[1], 1)

    def test_detect_fh6(self):
        payload = core.load_json(FH6_SAMPLE)
        result = core.detect_format(payload)
        self.assertEqual(result.format_name, "fh6")
        self.assertEqual(result.shape_count, 1850)
        self.assertIsNone(result.canvas)
        self.assertEqual(result.type_counts, {1: 237, 16: 257, 103: 241, 228: 1115})

    def test_detect_fh5_full_codes(self):
        payload = {
            "shapes": [
                {"type": 1048677, "data": [10, 20, 5, 5, 0], "color": [1, 2, 3, 255], "score": 0},
                {"type": 1048804, "data": [30, 40, 5, 5, 0], "color": [4, 5, 6, 255], "score": 0},
            ]
        }
        result = core.detect_format(payload)
        self.assertEqual(result.format_name, "fh5")

    def test_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("{not json", encoding="utf-8")
            with self.assertRaises(core.FormatError):
                core.load_json(str(bad))

    def test_missing_shapes(self):
        with self.assertRaises(core.FormatError):
            core.detect_format({"foo": []})

    def test_detect_fh6_native_dump(self):
        payload = {
            "format": "fh6_native_dump_v1",
            "game": "fh6",
            "pid": 1234,
            "layer_count": 2,
            "shapes": [
                {"type": 1048677, "data": [10, 20, 2.0, 1.0, 90, 0, 0], "color": [1, 2, 3, 255], "score": 0},
                {"type": 1048678, "data": [30, 40, 1.0, 2.0, 0, 0, 1], "color": [4, 5, 6, 255], "score": 0},
            ],
        }
        result = core.detect_format(payload)
        self.assertEqual(result.format_name, "fh6_native")
        self.assertEqual(result.shape_count, 2)


class TestConversion(unittest.TestCase):
    def test_fh5_to_fh6(self):
        payload = core.load_json(FH5_SAMPLE)
        result = core.fh5_to_fh6(payload)
        shapes = result.payload["shapes"]
        self.assertEqual(len(shapes), 2299)
        self.assertEqual(result.shape_count, 2299)
        # 画布元素应被移除：不应再有 4 值 type=1
        for shape in shapes:
            self.assertNotEqual(len(shape["data"]), 4)
            self.assertEqual(shape["type"], 16)
        # 与源形状逐一对比（跳过画布）
        source_shapes = core.extract_shapes(payload)[1:]
        for src, out in zip(source_shapes, shapes):
            self.assertEqual(out["type"], 16)
            self.assertEqual(len(out["data"]), 5)
            self.assertEqual(out["color"][:3], src["color"][:3])

    def test_fh6_to_fh5(self):
        payload = core.load_json(FH6_SAMPLE)
        result = core.fh6_to_fh5(payload)
        shapes = result.payload["shapes"]
        self.assertEqual(len(shapes), 1851)  # 画布 + 1850
        self.assertEqual(result.shape_count, 1850)
        # 首元素为画布
        canvas = shapes[0]
        self.assertTrue(core.is_canvas_sentinel(canvas))
        self.assertEqual(canvas["color"], [255, 0, 255, 0])
        # 类型映射：矩形1→1048677、椭圆16→1048678、三角形103→1048679、软边椭圆228→1048804
        types = {s["type"] for s in shapes[1:]}
        self.assertEqual(types, {1048677, 1048678, 1048679, 1048804})
        # 各类型数量按映射关系与源文件一致
        expected_type_counts = {}
        for s in core.extract_shapes(payload):
            mapped = core.FH5_TYPE_MAP[s["type"]]
            expected_type_counts[mapped] = expected_type_counts.get(mapped, 0) + 1
        out_type_counts = {}
        for s in shapes[1:]:
            out_type_counts[s["type"]] = out_type_counts.get(s["type"], 0) + 1
        self.assertEqual(out_type_counts, expected_type_counts)
        # 数据为游戏内存坐标 [x, -y, w/div, h/div, (360-rot)%360, 0, 0]
        src_shapes = core.extract_shapes(payload)
        for src, out in zip(src_shapes, shapes[1:]):
            x, y, w, h, rot = [float(v) for v in src["data"][:5]]
            divisor = core.scale_divisor(src["type"])
            expected = [x, -y, w / divisor, h / divisor, (360.0 - rot) % 360.0, 0.0, 0.0]
            for got, want in zip(out["data"], expected):
                self.assertAlmostEqual(float(got), want, delta=1e-6)
        # 警告包含类型映射与坐标换算说明
        codes = {w[0] for w in result.warnings}
        self.assertIn("warn.types_mapped", codes)
        self.assertIn("warn.canvas_added", codes)
        self.assertIn("warn.coords_to_memory", codes)
        # 颜色与数量保持
        for src, out in zip(src_shapes, shapes[1:]):
            self.assertEqual(out["color"], src["color"])

    def test_roundtrip_preserves_drawables(self):
        payload = core.load_json(FH5_SAMPLE)
        first = core.fh5_to_fh6(payload)      # FH6 小类型码 + 像素坐标
        mid = core.fh6_to_fh5(first.payload)  # FH5 完整类型码 + 内存坐标
        back = core.fh5_to_fh6(mid.payload)   # FH6 小类型码 + 像素坐标（还原）
        drawables = back.payload["shapes"]
        source = core.extract_shapes(payload)[1:]
        self.assertEqual(len(drawables), len(source))
        for src, out in zip(source, drawables):
            self.assertAlmostEqual(float(out["data"][0]), float(src["data"][0]), delta=1e-4)
            self.assertAlmostEqual(float(out["data"][1]), float(src["data"][1]), delta=1e-4)
            self.assertAlmostEqual(float(out["data"][2]), float(src["data"][2]), delta=1e-4)
            self.assertAlmostEqual(float(out["data"][3]), float(src["data"][3]), delta=1e-4)
            # 旋转角等价（360° 与 0° 等价），按 360 取模比较
            self.assertAlmostEqual(float(out["data"][4]) % 360.0, float(src["data"][4]) % 360.0, delta=1e-3)
            self.assertEqual(out["color"], src["color"])

    def test_roundtrip_full_codes_restore_types(self):
        payload = core.load_json(FH6_SAMPLE)
        to_fh5 = core.fh6_to_fh5(payload)
        to_fh6 = core.fh5_to_fh6(to_fh5.payload)
        source_types = [s["type"] for s in core.extract_shapes(payload)]
        roundtrip_types = [s["type"] for s in to_fh6.payload["shapes"]]
        self.assertEqual(roundtrip_types, source_types)

    def test_unknown_type_passthrough(self):
        payload = {
            "shapes": [
                {"type": 999, "data": [1, 2, 3, 4, 5], "color": [1, 2, 3, 255], "score": 0},
            ]
        }
        result = core.fh5_to_fh6(payload)
        self.assertEqual(result.payload["shapes"][0]["type"], 999)
        self.assertTrue(any(w[0] == "warn.shape_unknown" and w[1]["type"] == 999 for w in result.warnings))

    def test_native_fh6_to_fh5(self):
        payload = {
            "format": "fh6_native_dump_v1",
            "game": "fh6",
            "pid": 1234,
            "layer_count": 2,
            "shapes": [
                # 矩形：type 完整码 + 内存坐标（w=2 像素、h=1 像素，除数为 127）
                {"type": 1048677, "data": [10, 20, 2.0, 1.0, 90, 0, 0], "color": [1, 2, 3, 255], "score": 0},
                # 椭圆：type 完整码 + 内存坐标（w=1 像素、h=2 像素，除数为 63）
                {"type": 1048678, "data": [30, 40, 1.0, 2.0, 0, 0, 1], "color": [4, 5, 6, 255], "score": 0},
            ],
        }
        result = core.native_fh6_to_fh5(payload)
        shapes = result.payload["shapes"]
        self.assertEqual(len(shapes), 3)  # 画布 + 2 形状
        self.assertTrue(core.is_canvas_sentinel(shapes[0]))
        # 类型码原样保留
        self.assertEqual(shapes[1]["type"], 1048677)
        self.assertEqual(shapes[2]["type"], 1048678)
        # data 原样保留（已是 FH5 内存坐标）
        self.assertEqual(shapes[1]["data"], [10, 20, 2.0, 1.0, 90, 0, 0])
        self.assertEqual(shapes[2]["data"], [30, 40, 1.0, 2.0, 0, 0, 1])
        # 画布覆盖所有形状的像素外接范围
        canvas_w, canvas_h = shapes[0]["data"][2], shapes[0]["data"][3]
        self.assertGreaterEqual(canvas_w, 10 + 2 * 127)
        self.assertGreaterEqual(canvas_h, 20 + 1 * 127)
        self.assertGreaterEqual(canvas_w, 30 + 1 * 63)
        self.assertGreaterEqual(canvas_h, 40 + 2 * 63)


class TestEdgeCases(unittest.TestCase):
    def test_canvas_inference_empty(self):
        with self.assertRaises(core.FormatError):
            core.infer_canvas_size([])

    def test_triangle_scale_divisor(self):
        # 矩形 127，椭圆 63
        self.assertEqual(core.scale_divisor(core.FH6_RECT), 127.0)
        self.assertEqual(core.scale_divisor(core.FH5_RECT), 127.0)
        self.assertEqual(core.scale_divisor(core.FH6_ELLIPSE), 63.0)
        self.assertEqual(core.scale_divisor(core.FH5_ELLIPSE), 63.0)
        # 三角形默认 59%（正常），除数应为 63/0.59
        self.assertAlmostEqual(core.scale_divisor(core.FH6_TRIANGLE), 63.0 / 0.59, delta=1e-9)
        self.assertAlmostEqual(core.scale_divisor(core.FH5_TRIANGLE), 63.0 / 0.59, delta=1e-9)
        # 除数随比例线性缩放（59% 为锚点）
        anchor = core.scale_divisor(core.FH6_TRIANGLE, 0.59)
        for factor in (0.40, 0.45, 0.59, 0.65):
            divisor = core.scale_divisor(core.FH6_TRIANGLE, factor)
            self.assertAlmostEqual(divisor, anchor * factor / 0.59, delta=1e-9)
        # 比例越大，scale 越小（图形越小）
        scales = [
            core.pixel_to_memory([0, 0, 63, 63, 0], core.scale_divisor(core.FH6_TRIANGLE, f))[2]
            for f in (0.40, 0.45, 0.59, 0.65)
        ]
        self.assertEqual(scales, sorted(scales, reverse=True))

    def test_canvas_sentinel_recognition(self):
        good = {"type": 1, "data": [0, 0, 591, 714], "color": [255, 0, 255, 0], "score": 0}
        self.assertTrue(core.is_canvas_sentinel(good))
        bad_xy = {"type": 1, "data": [5, 0, 591, 714], "color": [255, 0, 255, 0], "score": 0}
        self.assertFalse(core.is_canvas_sentinel(bad_xy))
        bad_len = {"type": 1, "data": [0, 0, 591, 714, 0], "color": [255, 0, 255, 0], "score": 0}
        self.assertFalse(core.is_canvas_sentinel(bad_len))
        opaque = {"type": 1, "data": [0, 0, 591, 714], "color": [255, 0, 255, 255], "score": 0}
        self.assertFalse(core.is_canvas_sentinel(opaque))

    def test_convert_file_roundtrip_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            mid = tmp / "mid.json"
            final = tmp / "final.json"
            result = core.convert_file(FH5_SAMPLE, str(mid), "fh5_to_fh6")
            self.assertTrue(mid.is_file())
            self.assertEqual(len(result.payload["shapes"]), 2299)
            result2 = core.convert_file(str(mid), str(final), "fh6_to_fh5")
            self.assertTrue(final.is_file())
            data = json.loads(final.read_text(encoding="utf-8"))
            self.assertTrue(core.is_canvas_sentinel(data["shapes"][0]))

    def test_fh5_writer_matches_native_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            result = core.convert_file(FH6_SAMPLE, str(out), "fh6_to_fh5")
            raw = out.read_bytes()
            text = raw.decode("ascii")
            # 与 forza-painter.exe 原生格式一致：
            # 首行 {"shapes":，末行 ]}，每个形状一行，CRLF 行尾
            self.assertTrue(text.startswith('{"shapes":\r\n['))
            self.assertTrue(text.endswith("\r\n]}"))
            lines = text.split("\r\n")
            # 头 + (画布 + N 形状) + 尾
            self.assertEqual(len(lines), len(result.payload["shapes"]) + 2)
            self.assertNotIn(b"\r\r", raw)
            # 每行形状都是紧凑 JSON
            self.assertTrue(lines[1].startswith("[{"))
            for line in lines[2:-1]:
                self.assertTrue(line.startswith("{"))
                self.assertIn('"type":', line)
                self.assertIn('"data":[', line)


if __name__ == "__main__":
    unittest.main(verbosity=2)
