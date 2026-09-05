# -*- coding: utf-8 -*-
"""应用多语言支持：简体中文 / English / 日本語 / 한국어。"""

from __future__ import annotations

from typing import Any, Dict

LANG_CODES = ("zh", "en", "ja", "ko")
LANG_NAMES = {
    "zh": "简体中文",
    "en": "English",
    "ja": "日本語",
    "ko": "한국어",
}

MESSAGES: Dict[str, Dict[str, str]] = {
    # ---------------- 应用窗口 ----------------
    "app.title": {
        "zh": "Forza 涂装 JSON 转换器（FH5 ↔ FH6）",
        "en": "Forza Livery JSON Converter (FH5 ↔ FH6)",
        "ja": "Forza リバリー JSON コンバーター（FH5 ↔ FH6）",
        "ko": "Forza 리버리 JSON 변환기 (FH5 ↔ FH6)",
    },
    "app.version": {"zh": "v1.1.0", "en": "v1.1.0", "ja": "v1.1.0", "ko": "v1.1.0"},
    "label.theme": {"zh": "主题：", "en": "Theme:", "ja": "テーマ：", "ko": "테마:"},
    "theme.system": {"zh": "跟随系统", "en": "System", "ja": "システムに従う", "ko": "시스템 따라가기"},
    "theme.light": {"zh": "浅色", "en": "Light", "ja": "ライト", "ko": "라이트"},
    "theme.dark": {"zh": "深色", "en": "Dark", "ja": "ダーク", "ko": "다크"},
    "label.language": {"zh": "语言：", "en": "Language:", "ja": "言語：", "ko": "언어:"},
    "section.file": {"zh": "文件", "en": "File", "ja": "ファイル", "ko": "파일"},
    "drop.hint": {
        "zh": "将 .json 文件拖入此区域\n\n或点击下方按钮选择文件",
        "en": "Drop a .json file here\n\nor click the button below to choose a file",
        "ja": "ここに .json ファイルをドラッグ\n\nまたは下のボタンでファイルを選択",
        "ko": "여기에 .json 파일을 끌어다 놓으세요\n\n또는 아래 버튼으로 파일 선택",
    },
    "btn.choose": {"zh": "选择文件…", "en": "Choose File…", "ja": "ファイルを選択…", "ko": "파일 선택…"},
    "btn.clear": {"zh": "清空", "en": "Clear", "ja": "クリア", "ko": "지우기"},
    "section.info": {"zh": "文件信息", "en": "File Info", "ja": "ファイル情報", "ko": "파일 정보"},
    "info.file": {"zh": "文件：", "en": "File:", "ja": "ファイル：", "ko": "파일:"},
    "info.format": {"zh": "识别格式：", "en": "Detected:", "ja": "検出形式：", "ko": "감지 형식:"},
    "info.shapes": {"zh": "形状数量：", "en": "Shapes:", "ja": "シェイプ数：", "ko": "도형 수:"},
    "info.canvas": {"zh": "画布尺寸：", "en": "Canvas:", "ja": "キャンバス：", "ko": "캔버스:"},
    "info.types": {"zh": "类型分布：", "en": "Type counts:", "ja": "タイプ分布：", "ko": "유형 분포:"},
    "section.warnings": {
        "zh": "格式提醒（仅提示，不阻止转换）",
        "en": "Format notes (warnings only, conversion is not blocked)",
        "ja": "形式メモ（警告のみ、変換はブロックされません）",
        "ko": "형식 메모 (경고만 표시, 변환은 차단되지 않음)",
    },
    "section.direction": {"zh": "转换方向", "en": "Direction", "ja": "変換方向", "ko": "변환 방향"},
    "dir.fh5_to_fh6": {
        "zh": "FH5 → FH6（ForzaPainter 转 Vinylizer）",
        "en": "FH5 → FH6 (ForzaPainter to Vinylizer)",
        "ja": "FH5 → FH6（ForzaPainter → Vinylizer）",
        "ko": "FH5 → FH6 (ForzaPainter → Vinylizer)",
    },
    "dir.fh6_to_fh5": {
        "zh": "FH6 → FH5（Vinylizer 转 ForzaPainter）",
        "en": "FH6 → FH5 (Vinylizer to ForzaPainter)",
        "ja": "FH6 → FH5（Vinylizer → ForzaPainter）",
        "ko": "FH6 → FH5 (Vinylizer → ForzaPainter)",
    },
    "btn.convert": {"zh": "开始转换", "en": "Convert", "ja": "変換開始", "ko": "변환 시작"},
    "status.ready": {
        "zh": "就绪：请拖入 JSON 文件，或点击“选择文件”。",
        "en": "Ready: drop a JSON file, or click “Choose File”.",
        "ja": "準備完了：JSON ファイルをドラッグするか「ファイルを選択」をクリック。",
        "ko": "준비됨: JSON 파일을 끌어다 놓거나 '파일 선택'을 클릭하세요.",
    },
    "status.no_dnd": {
        "zh": "未安装拖放组件，拖放不可用（仍可使用“选择文件”）。",
        "en": "Drag-and-drop component missing; use “Choose File” instead.",
        "ja": "ドラッグ＆ドロップが利用できません。「ファイルを選択」を使用してください。",
        "ko": "끌어다 놓기를 사용할 수 없습니다. '파일 선택'을 이용하세요.",
    },
    "status.multi_drop": {
        "zh": "检测到 {count} 个文件，本次仅处理第一个。",
        "en": "{count} files detected; only the first is processed.",
        "ja": "{count} 個のファイルを検出、最初の 1 つのみ処理します。",
        "ko": "{count}개 파일이 감지되었습니다. 첫 번째 파일만 처리합니다.",
    },
    "status.cleared": {"zh": "已清空。", "en": "Cleared.", "ja": "クリアしました。", "ko": "지웠습니다."},
    "status.parse_failed": {"zh": "文件解析失败。", "en": "Failed to parse file.", "ja": "ファイル解析に失敗しました。", "ko": "파일 분석에 실패했습니다."},
    "status.loaded": {
        "zh": "文件已载入，格式识别完成。可修改转换方向后开始转换。",
        "en": "File loaded and format detected. Adjust direction if needed, then convert.",
        "ja": "ファイルを読み込み、形式を検出しました。必要に応じて変換方向を変更してください。",
        "ko": "파일이 로드되고 형식이 감지되었습니다. 필요시 방향을 변경한 후 변환하세요.",
    },
    "status.manual_direction": {
        "zh": "无法自动判定来源，请手动选择转换方向。",
        "en": "Could not auto-detect the source format; choose the direction manually.",
        "ja": "形式を自動判定できません。変換方向を手動で選択してください。",
        "ko": "형식을 자동으로 판별할 수 없습니다. 변환 방향을 직접 선택하세요.",
    },
    "status.cancelled": {"zh": "已取消保存，未进行转换。", "en": "Save cancelled; nothing converted.", "ja": "保存をキャンセルしました。", "ko": "저장이 취소되었습니다."},
    "status.converting": {"zh": "正在转换 → {target} …", "en": "Converting → {target} …", "ja": "変換中 → {target} …", "ko": "변환 중 → {target} …"},
    "status.done": {
        "zh": "转换完成：{source} → {target}，共 {count} 个形状。",
        "en": "Done: {source} → {target}, {count} shapes.",
        "ja": "変換完了：{source} → {target}、{count} シェイプ。",
        "ko": "변환 완료: {source} → {target}, {count}개 도형.",
    },
    "status.convert_failed": {"zh": "转换失败。", "en": "Conversion failed.", "ja": "変換に失敗しました。", "ko": "변환에 실패했습니다."},
    "status.theme_changed": {"zh": "主题已切换为：{theme}。", "en": "Theme changed: {theme}.", "ja": "テーマ変更：{theme}。", "ko": "테마 변경: {theme}."},
    "status.language_changed": {"zh": "语言已切换为：{language}。", "en": "Language changed: {language}.", "ja": "言語変更：{language}。", "ko": "언어 변경: {language}."},
    "no_warnings": {"zh": "（无提醒）", "en": "(no notes)", "ja": "（メモなし）", "ko": "(메모 없음)"},
    "msg.choose_first": {
        "zh": "请先选择或拖入一个 JSON 文件。",
        "en": "Please choose or drop a JSON file first.",
        "ja": "先に JSON ファイルを選択またはドラッグしてください。",
        "ko": "먼저 JSON 파일을 선택하거나 끌어다 놓으세요.",
    },
    "dialog.save_title": {
        "zh": "选择转换后文件的名称与保存位置",
        "en": "Choose the output file name and location",
        "ja": "変換後のファイル名と保存先を選択",
        "ko": "변환된 파일의 이름과 저장 위치 선택",
    },
    "dialog.success_title": {"zh": "转换成功", "en": "Conversion Succeeded", "ja": "変換成功", "ko": "변환 성공"},
    "dialog.success_body": {
        "zh": "转换成功！\n\n已保存 {count} 个形状到：\n{path}",
        "en": "Conversion succeeded!\n\nSaved {count} shapes to:\n{path}",
        "ja": "変換に成功しました！\n\n{count} シェイプを保存しました：\n{path}",
        "ko": "변환에 성공했습니다!\n\n{count}개 도형을 저장했습니다:\n{path}",
    },
    "dialog.error_title": {"zh": "转换失败", "en": "Conversion Failed", "ja": "変換失敗", "ko": "변환 실패"},
    "dialog.error_body": {
        "zh": "转换过程中出现错误：\n\n{error}\n\n请检查源文件与保存路径后重试。",
        "en": "An error occurred during conversion:\n\n{error}\n\nCheck the source file and save path, then retry.",
        "ja": "変換中にエラーが発生しました：\n\n{error}\n\n元ファイルと保存先を確認して再試行してください。",
        "ko": "변환 중 오류가 발생했습니다:\n\n{error}\n\n원본 파일과 저장 경로를 확인한 후 다시 시도하세요.",
    },
    "filetype.json": {"zh": "JSON 文件", "en": "JSON files", "ja": "JSON ファイル", "ko": "JSON 파일"},
    "filetype.all": {"zh": "所有文件", "en": "All files", "ja": "すべてのファイル", "ko": "모든 파일"},
    "fmt.fh5": {"zh": "FH5（ForzaPainter）", "en": "FH5 (ForzaPainter)", "ja": "FH5（ForzaPainter）", "ko": "FH5 (ForzaPainter)"},
    "fmt.fh6": {"zh": "FH6（Vinylizer）", "en": "FH6 (Vinylizer)", "ja": "FH6（Vinylizer）", "ko": "FH6 (Vinylizer)"},
    "fmt.unknown": {"zh": "未知（无法判定）", "en": "Unknown", "ja": "不明", "ko": "알 수 없음"},
    "info.none": {"zh": "--", "en": "--", "ja": "--", "ko": "--"},
    "info.canvas_none": {
        "zh": "无（FH6 格式不含画布元素）",
        "en": "None (FH6 format has no canvas element)",
        "ja": "なし（FH6 形式にキャンバス要素はありません）",
        "ko": "없음 (FH6 형식에는 캔버스 요소가 없음)",
    },
    "info.canvas_fh5": {
        "zh": "[0, 0, {w}, {h}]（FH5 画布）",
        "en": "[0, 0, {w}, {h}] (FH5 canvas)",
        "ja": "[0, 0, {w}, {h}]（FH5 キャンバス）",
        "ko": "[0, 0, {w}, {h}] (FH5 캔버스)",
    },
    "info.no_file": {"zh": "未选择文件", "en": "No file selected", "ja": "ファイル未選択", "ko": "선택된 파일 없음"},
    # ---------------- 核心错误 ----------------
    "err.json_parse": {
        "zh": "JSON 解析失败（第 {line} 行第 {col} 列）：{msg}",
        "en": "JSON parse error (line {line}, column {col}): {msg}",
        "ja": "JSON 解析エラー（{line} 行目 {col} 列目）：{msg}",
        "ko": "JSON 파싱 오류 ({line}행 {col}열): {msg}",
    },
    "err.file_read": {
        "zh": "无法读取文件：{err}",
        "en": "Cannot read file: {err}",
        "ja": "ファイルを読み込めません：{err}",
        "ko": "파일을 읽을 수 없음: {err}",
    },
    "err.top_level": {
        "zh": "JSON 顶层必须是对象（包含 shapes 数组）或数组。",
        "en": "The JSON top level must be an object (with a shapes array) or an array.",
        "ja": "JSON の最上位はオブジェクト（shapes 配列を含む）または配列である必要があります。",
        "ko": "JSON 최상위는 객체(shapes 배열 포함) 또는 배열이어야 합니다.",
    },
    "err.no_shapes_key": {
        "zh": "JSON 中找不到 shapes 数组（字段名应为 \"shapes\"）。",
        "en": "No shapes array found in JSON (expected key: \"shapes\").",
        "ja": "JSON に shapes 配列が見つかりません（キーは \"shapes\" である必要があります）。",
        "ko": "JSON에서 shapes 배열을 찾을 수 없습니다 (키: \"shapes\").",
    },
    "err.empty_shapes": {
        "zh": "shapes 数组为空，无法转换。",
        "en": "The shapes array is empty; nothing to convert.",
        "ja": "shapes 配列が空です。変換できません。",
        "ko": "shapes 배열이 비어 있어 변환할 수 없습니다.",
    },
    "err.no_valid_type": {
        "zh": "shapes 中找不到有效的 type 字段。",
        "en": "No valid type field found in shapes.",
        "ja": "shapes に有効な type フィールドがありません。",
        "ko": "shapes에 유효한 type 필드가 없습니다.",
    },
    "err.no_drawables": {
        "zh": "没有可转换的有效形状。",
        "en": "No valid shapes to convert.",
        "ja": "変換できる有効なシェイプがありません。",
        "ko": "변환할 유효한 도형이 없습니다.",
    },
    "err.canvas_infer": {
        "zh": "没有可用于推断画布尺寸的形状。",
        "en": "No shapes available to infer the canvas size.",
        "ja": "キャンバスサイズを推定できるシェイプがありません。",
        "ko": "캔버스 크기를 추정할 도형이 없습니다.",
    },
    "err.bad_direction": {
        "zh": "未知转换方向：{direction}",
        "en": "Unknown conversion direction: {direction}",
        "ja": "不明な変換方向：{direction}",
        "ko": "알 수 없는 변환 방향: {direction}",
    },
    # ---------------- 核心警告 ----------------
    "warn.unknown_types": {
        "zh": "存在未定义的类型码：{types}（不属于已知类型 1/16/103/228），这些元素将原样保留。",
        "en": "Unknown type codes present: {types} (not in known set 1/16/103/228); these elements are kept as-is.",
        "ja": "未定義のタイプコード：{types}（既知の 1/16/103/228 以外）。これらの要素はそのまま保持されます。",
        "ko": "정의되지 않은 유형 코드: {types} (알려진 1/16/103/228 외). 해당 요소는 그대로 유지됩니다.",
    },
    "warn.canvas_found": {
        "zh": "检测到 FH5 画布描述元素（type=1 且 data 为 [0,0,W,H]）。",
        "en": "FH5 canvas element detected (type=1 with data [0,0,W,H]).",
        "ja": "FH5 キャンバス要素を検出（type=1、data [0,0,W,H]）。",
        "ko": "FH5 캔버스 요소 감지 (type=1, data [0,0,W,H]).",
    },
    "warn.only_canvas": {
        "zh": "仅有一个 4 值 type=1 元素：可能是孤立的 FH5 画布描述，无法推断具体格式。",
        "en": "Only one 4-value type=1 element: possibly a lone FH5 canvas; format cannot be determined.",
        "ja": "4 値 type=1 の要素が 1 つだけ：孤立した FH5 キャンバスと思われ、形式を判定できません。",
        "ko": "4값 type=1 요소가 하나뿐입니다: 고립된 FH5 캔버스로 보이며 형식을 판별할 수 없습니다.",
    },
    "warn.rect4": {
        "zh": "存在 4 值 data 的矩形元素（FH6 旧版特征）。",
        "en": "Rectangle elements with 4-value data detected (legacy FH6 style).",
        "ja": "4 値 data の矩形要素があります（旧 FH6 形式の特徴）。",
        "ko": "4값 data의 사각형 요소가 있습니다 (구형 FH6 스타일).",
    },
    "warn.ambiguous": {
        "zh": "无法自动判定 FH5/FH6 格式，请手动选择转换方向。",
        "en": "Could not auto-detect FH5/FH6; choose the direction manually.",
        "ja": "FH5/FH6 を自動判定できません。変換方向を手動で選択してください。",
        "ko": "FH5/FH6을 자동 판별할 수 없습니다. 변환 방향을 직접 선택하세요.",
    },
    "warn.unknown_without_canvas": {
        "zh": "没有画布元素且包含未知类型码，无法自动判定 FH5/FH6，请手动选择转换方向。",
        "en": "No canvas element and unknown type codes present; choose the direction manually.",
        "ja": "キャンバス要素がなく未知のタイプコードを含むため、変換方向を手動で選択してください。",
        "ko": "캔버스 요소가 없고 알 수 없는 유형 코드가 있어 방향을 직접 선택하세요.",
    },
    "warn.canvas_removed": {
        "zh": "已移除 FH5 画布描述元素（FH6 格式不含画布元素）。",
        "en": "FH5 canvas element removed (FH6 format has no canvas element).",
        "ja": "FH5 キャンバス要素を削除しました（FH6 形式にはキャンバス要素がありません）。",
        "ko": "FH5 캔버스 요소가 제거되었습니다 (FH6 형식에는 캔버스 요소가 없음).",
    },
    "warn.no_canvas_found": {
        "zh": "未发现 FH5 画布描述元素，已按原样输出全部元素。",
        "en": "No FH5 canvas element found; all elements written as-is.",
        "ja": "FH5 キャンバス要素が見つからないため、全要素をそのまま出力しました。",
        "ko": "FH5 캔버스 요소를 찾지 못해 모든 요소를 그대로 출력했습니다.",
    },
    "warn.shape_unknown": {
        "zh": "第 {index} 个元素类型 {type} 未定义，已原样保留（可能无法在目标工具中识别）。",
        "en": "Element {index} has undefined type {type}; kept as-is (may be unrecognized by the target tool).",
        "ja": "{index} 番目の要素のタイプ {type} は未定義のため、そのまま保持（対象ツールで認識されない可能性があります）。",
        "ko": "{index}번째 요소의 유형 {type}이 정의되지 않아 그대로 유지합니다 (대상 도구에서 인식되지 않을 수 있음).",
    },
    "warn.shape_skipped": {
        "zh": "第 {index} 个元素不是有效形状（缺少 type/data/color），已跳过。",
        "en": "Element {index} is not a valid shape (missing type/data/color); skipped.",
        "ja": "{index} 番目の要素は有効なシェイプではありません（type/data/color 不足）。スキップしました。",
        "ko": "{index}번째 요소가 유효한 도형이 아닙니다 (type/data/color 부족). 건너뜁니다.",
    },
    "warn.types_mapped": {
        "zh": "已按映射表转换图形类型：矩形→1048677、椭圆→1048678、三角形→1048679、软边椭圆→1048804。",
        "en": "Shape types mapped: rectangle→1048677, ellipse→1048678, triangle→1048679, soft ellipse→1048804.",
        "ja": "シェイプタイプを変換：矩形→1048677、楕円→1048678、三角形→1048679、ソフト楕円→1048804。",
        "ko": "도형 유형 변환: 사각형→1048677, 타원→1048678, 삼각형→1048679, 소프트 타원→1048804.",
    },
    "warn.canvas_added": {
        "zh": "已添加 FH5 画布描述元素 [0, 0, {width}, {height}]（尺寸由形状外接范围推断）。",
        "en": "FH5 canvas element [0, 0, {width}, {height}] added (size inferred from shape bounds).",
        "ja": "FH5 キャンバス要素 [0, 0, {width}, {height}] を追加（シェイプの外接範囲から推定）。",
        "ko": "FH5 캔버스 요소 [0, 0, {width}, {height}] 추가 (도형 범위에서 추정).",
    },
    "warn.coords_to_memory": {
        "zh": "已将像素坐标换算为 FH5 游戏内存坐标（x、-y、宽高/基础尺寸、旋转角取反）。",
        "en": "Pixel coordinates converted to FH5 game-memory coordinates (x, -y, size/base-size, flipped rotation).",
        "ja": "ピクセル座標を FH5 ゲームメモリ座標に変換しました（x、-y、サイズ/基準サイズ、回転反転）。",
        "ko": "픽셀 좌표를 FH5 게임 메모리 좌표로 변환했습니다 (x, -y, 크기/기준 크기, 회전 반전).",
    },
    "warn.input_canvas_skipped": {
        "zh": "输入已包含 FH5 画布描述元素，不再重复添加。",
        "en": "Input already contains an FH5 canvas element; not adding another.",
        "ja": "入力に FH5 キャンバス要素が既にあるため、追加しません。",
        "ko": "입력에 FH5 캔버스 요소가 이미 있어 추가하지 않습니다.",
    },
    "note.fh5_target": {
        "zh": "将移除 FH5 画布描述元素，其余形状原样输出为 FH6 格式。",
        "en": "The FH5 canvas element will be removed; remaining shapes are output in FH6 format.",
        "ja": "FH5 キャンバス要素を削除し、残りのシェイプを FH6 形式で出力します。",
        "ko": "FH5 캔버스 요소를 제거하고 나머지 도형을 FH6 형식으로 출력합니다.",
    },
    "note.fh6_target": {
        "zh": "将添加 FH5 画布描述元素；按映射表转换类型（1→1048677、16→1048678、103→1048679、228→1048804），并把像素坐标换算为游戏内存坐标。",
        "en": "An FH5 canvas element will be added; types are mapped (1→1048677, 16→1048678, 103→1048679, 228→1048804) and pixel coordinates are converted to game-memory coordinates.",
        "ja": "FH5 キャンバス要素を追加し、タイプを変換（1→1048677、16→1048678、103→1048679、228→1048804）、ピクセル座標をゲームメモリ座標に変換します。",
        "ko": "FH5 캔버스 요소를 추가하고 유형을 변환(1→1048677, 16→1048678, 103→1048679, 228→1048804)하며 픽셀 좌표를 게임 메모리 좌표로 변환합니다.",
    },
    # ---------------- 设置 ----------------
    "btn.settings": {"zh": "设置", "en": "Settings", "ja": "設定", "ko": "설정"},
    "settings.title": {"zh": "设置", "en": "Settings", "ja": "設定", "ko": "설정"},
    "settings.language": {"zh": "语言", "en": "Language", "ja": "言語", "ko": "언어"},
    "settings.theme": {"zh": "主题", "en": "Theme", "ja": "テーマ", "ko": "테마"},
    "settings.background": {"zh": "背景图片", "en": "Background image", "ja": "背景画像", "ko": "배경 이미지"},
    "settings.background_hint": {
        "zh": "选择一个本地图片作为应用背景（填充铺满、不拉伸）",
        "en": "Choose a local image as the app background (filled, no stretching)",
        "ja": "アプリ背景に使用するローカル画像を選択（引き伸ばしなしで全体に配置）",
        "ko": "앱 배경으로 사용할 로컬 이미지 선택 (늘림 없이 채움)",
    },
    "settings.opacity": {"zh": "背景不透明度", "en": "Background opacity", "ja": "背景の不透明度", "ko": "배경 불투명도"},
    "settings.choose_image": {"zh": "选择图片…", "en": "Choose image…", "ja": "画像を選択…", "ko": "이미지 선택…"},
    "settings.clear_image": {"zh": "清除背景", "en": "Clear background", "ja": "背景を消去", "ko": "배경 지우기"},
    "settings.no_image": {"zh": "未设置", "en": "None", "ja": "なし", "ko": "없음"},
    "settings.close": {"zh": "关闭", "en": "Close", "ja": "閉じる", "ko": "닫기"},
    "status.bg_changed": {"zh": "背景已更新。", "en": "Background updated.", "ja": "背景を更新しました。", "ko": "배경이 업데이트되었습니다."},
    "status.bg_cleared": {"zh": "背景已清除。", "en": "Background cleared.", "ja": "背景を消去しました。", "ko": "배경을 지웠습니다."},
    "status.bg_error": {
        "zh": "背景图片加载失败：{error}",
        "en": "Failed to load background image: {error}",
        "ja": "背景画像の読み込みに失敗：{error}",
        "ko": "배경 이미지 로드 실패: {error}",
    },
    # ---------------- 三角形大小调节 ----------------
    "section.triangle_size": {
        "zh": "调节三角形的大小",
        "en": "Adjust triangle size",
        "ja": "三角形のサイズ調整",
        "ko": "삼각형 크기 조정",
    },
    "triangle.note": {
        "zh": "当彩绘纹饰导入出现异常时，可在此处调整三角形的大小并尝试重新导入。在调整后，可能仍需要进行少量的手工修正才能正常显示。",
        "en": "If the imported livery looks wrong, adjust the triangle size here and try importing again. Some manual touch-ups may still be needed afterwards.",
        "ja": "インポートしたリバリーが正常に表示されない場合は、ここで三角形のサイズを調整して再インポートしてください。調整後も、少量の手動修正が必要な場合があります。",
        "ko": "가져온 리버리가 비정상적으로 보일 경우 여기서 삼각형 크기를 조정하고 다시 가져오세요. 조정 후에도 약간의 수동 수정이 필요할 수 있습니다.",
    },
    "triangle.smaller": {"zh": "更小的三角形", "en": "Smaller triangle", "ja": "より小さい三角形", "ko": "더 작은 삼각형"},
    "triangle.small": {"zh": "较小的三角形", "en": "Small triangle", "ja": "小さい三角形", "ko": "작은 삼각형"},
    "triangle.normal": {"zh": "正常的三角形", "en": "Normal triangle", "ja": "通常の三角形", "ko": "보통 삼각형"},
    "triangle.larger": {"zh": "较大的三角形", "en": "Larger triangle", "ja": "大きい三角形", "ko": "큰 삼각형"},
    "note.only_fh6_to_fh5": {
        "zh": "此工具仅支持 FH6 → FH5 转换，检测到的是 FH5 文件。",
        "en": "This tool only supports FH6 → FH5 conversion; an FH5 file was detected.",
        "ja": "このツールは FH6 → FH5 変換のみ対応しています。FH5 ファイルが検出されました。",
        "ko": "이 도구는 FH6 → FH5 변환만 지원합니다. FH5 파일이 감지되었습니다.",
    },
    "err.only_fh6_to_fh5_supported": {
        "zh": "此工具仅支持 FH6 → FH5 转换。请载入 FH6 文件（Vinylizer 或 FH6 内存导出）后再转换。",
        "en": "This tool only supports FH6 → FH5 conversion. Load an FH6 file (Vinylizer or FH6 memory dump) first.",
        "ja": "このツールは FH6 → FH5 変換のみ対応しています。FH6 ファイル（Vinylizer または FH6 メモリエクスポート）を読み込んでから変換してください。",
        "ko": "이 도구는 FH6 → FH5 변환만 지원합니다. FH6 파일(Vinylizer 또는 FH6 메모리 덤프)을 먼저 불러오세요.",
    },
    "fmt.fh6_native": {
        "zh": "FH6 原生（内存导出）",
        "en": "FH6 Native (memory dump)",
        "ja": "FH6 ネイティブ（メモリエクスポート）",
        "ko": "FH6 네이티브 (메모리 덤프)",
    },
    "btn.dump_fh6": {
        "zh": "从FH6内存导出",
        "en": "Dump from FH6 memory",
        "ja": "FH6メモリからエクスポート",
        "ko": "FH6 메모리에서 내보내기",
    },
    "btn.refresh": {
        "zh": "刷新",
        "en": "Refresh",
        "ja": "更新",
        "ko": "새로 고침",
    },
    "dump.layer_count": {
        "zh": "图层数量（可选）",
        "en": "Layer count (optional)",
        "ja": "レイヤー数（任意）",
        "ko": "레이어 수 (선택)",
    },
    "dump.layer_count_hint": {
        "zh": "可选",
        "en": "Optional",
        "ja": "任意",
        "ko": "선택",
    },
    "dump.layer_count_invalid": {
        "zh": "图层数量必须是数字。",
        "en": "The layer count must be a number.",
        "ja": "レイヤー数は数字で入力してください。",
        "ko": "레이어 수는 숫자여야 합니다.",
    },
    "dialog.dump_save_title": {
        "zh": "保存导出的 FH6 原始 JSON",
        "en": "Save the exported FH6 raw JSON",
        "ja": "エクスポートした FH6 生 JSON を保存",
        "ko": "내보낸 FH6 원본 JSON 저장",
    },
    "dialog.dump_success_title": {
        "zh": "导出成功",
        "en": "Dump Succeeded",
        "ja": "エクスポート成功",
        "ko": "내보내기 성공",
    },
    "dialog.dump_success_body": {
        "zh": "已从 FH6 内存导出 {count} 个图层。\n\n已保存到：\n{path}\n\n文件已自动载入，可直接转换为 FH5。",
        "en": "Dumped {count} layers from FH6 memory.\n\nSaved to:\n{path}\n\nThe file was loaded automatically; you can now convert it to FH5.",
        "ja": "FH6 メモリから {count} レイヤーをエクスポートしました。\n\n保存先：\n{path}\n\nファイルを自動で読み込みました。そのまま FH5 に変換できます。",
        "ko": "FH6 메모리에서 {count}개 레이어를 내보냈습니다.\n\n저장 위치:\n{path}\n\n파일이 자동으로 로드되었으며, 바로 FH5로 변환할 수 있습니다.",
    },
    "status.dump_started": {
        "zh": "正在从 FH6 内存导出当前彩绘组…",
        "en": "Dumping the current livery group from FH6 memory…",
        "ja": "FH6 メモリから現在のリバリーグループをエクスポート中…",
        "ko": "FH6 메모리에서 현재 리버리 그룹을 내보내는 중…",
    },
    "status.dump_progress": {
        "zh": "{message}",
        "en": "{message}",
        "ja": "{message}",
        "ko": "{message}",
    },
    "status.dump_done": {
        "zh": "FH6 内存导出完成：共 {count} 个图层。",
        "en": "FH6 memory dump complete: {count} layers.",
        "ja": "FH6 メモリエクスポート完了：{count} レイヤー。",
        "ko": "FH6 메모리 내보내기 완료: {count}개 레이어.",
    },
    "status.dump_failed": {
        "zh": "FH6 内存导出失败。",
        "en": "FH6 memory dump failed.",
        "ja": "FH6 メモリエクスポートに失敗しました。",
        "ko": "FH6 메모리 내보내기에 실패했습니다.",
    },
    "status.dump_cancelled": {
        "zh": "FH6 内存导出已中断。",
        "en": "FH6 memory dump was cancelled.",
        "ja": "FH6 メモリエクスポートを中断しました。",
        "ko": "FH6 메모리 내보내기가 중단되었습니다.",
    },
    "status.dump_timeout": {
        "zh": "FH6 内存导出超时，已恢复按钮。可点击“刷新”重试。",
        "en": "FH6 memory dump timed out; buttons restored. Click “Refresh” to retry.",
        "ja": "FH6 メモリエクスポートがタイムアウトしました。ボタンを復旧しました。「更新」で再試行してください。",
        "ko": "FH6 메모리 내보내기 시간 초과. 버튼이 복구되었습니다. '새로 고침'을 눌러 다시 시도하세요.",
    },
    "status.convert_timeout": {
        "zh": "转换超时，已恢复按钮。",
        "en": "Conversion timed out; buttons restored.",
        "ja": "変換がタイムアウトしました。ボタンを復旧しました。",
        "ko": "변환 시간 초과. 버튼이 복구되었습니다.",
    },
    "status.refreshed": {
        "zh": "界面已刷新，可重新操作。",
        "en": "UI refreshed; ready to continue.",
        "ja": "画面を更新しました。再操作できます。",
        "ko": "화면이 새로 고침되었습니다. 다시 작업할 수 있습니다.",
    },
    "note.fh6_native_target": {
        "zh": "检测到 FH6 原生（内存导出）格式：将插入 FH5 画布元素，形状类型码与内存坐标保持原样。",
        "en": "FH6 native (memory dump) format detected: an FH5 canvas element will be added, and shape type codes / memory coordinates are preserved.",
        "ja": "FH6 ネイティブ（メモリエクスポート）形式を検出：FH5 キャンバス要素を追加し、シェイプのタイプコードとメモリ座標はそのまま保持します。",
        "ko": "FH6 네이티브(메모리 덤프) 형식이 감지되었습니다: FH5 캔버스 요소를 추가하고 도형 유형 코드와 메모리 좌표를 그대로 유지합니다.",
    },
}

_current_lang = "zh"


def set_language(code: str) -> None:
    global _current_lang
    if code in LANG_CODES:
        _current_lang = code


def get_language() -> str:
    return _current_lang


def get(key: str, **params: Any) -> str:
    entry = MESSAGES.get(key)
    if not entry:
        return key
    text = entry.get(_current_lang) or entry.get("zh") or key
    if params:
        try:
            text = text.format(**params)
        except (KeyError, IndexError, ValueError):
            pass
    return text


def get_in(code: str, lang: str, **params: Any) -> str:
    entry = MESSAGES.get(code)
    if not entry:
        return code
    text = entry.get(lang) or entry.get("zh") or code
    if params:
        try:
            text = text.format(**params)
        except (KeyError, IndexError, ValueError):
            pass
    return text
