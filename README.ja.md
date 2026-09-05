# Forza JSON Converter

Forza Horizon 6 / Forza Horizon 5 リバリー JSON 変換ツール（グラフィカルインターフェース）。

**Forza Horizon 6** のリバリー JSON を **Forza Horizon 5（forza-painter）** でインポート可能な JSON に変換します。実行中の FH6 プロセスから現在開いているリバリーグループをメモリ経由で直接エクスポートすることもできます。

## 機能

- ファイルのドラッグ＆ドロップ / ファイル選択
- FH5 / FH6 形式を自動判定して警告を表示（変換はブロックされません）
- FH6 → FH5 のワンクリック変換（長方形 / 楕円 / 三角形 / ソフト楕円のタイプマッピング）
- FH6 メモリから現在のリバリーグループをエクスポート（フルタイプコード + メモリ座標）
- 三角形サイズの調整（40% / 45% / 59% / 65%）
- ライト / ダークテーマ、Windows のシステムテーマに自動追従
- 簡体字中国語 / English / 日本語 / 한국어
- 背景画像と不透明度の設定

## ファイル構成

- `gui_app.py`: グラフィカルインターフェース
- `converter_core.py`: 形式判定と変換のコア
- `fh6_dump.py`: FH6 メモリ読み取りとエクスポート
- `i18n.py`: 多言語文字列
- `tests.py`: ユニットテスト
- `build_exe.ps1`: PyInstaller ビルドスクリプト
- `assets/app.ico`: アプリケーションアイコン

## exe のビルド

```powershell
powershell -ExecutionPolicy Bypass -File build_exe.ps1
```

ビルド結果は `dist/ForzaJSONConverter.exe` に出力されます。

## テストの実行

```powershell
python tests.py
```

## 依存関係

- Python 3.12+
- Pillow
- tkinterdnd2
- PyInstaller（ビルド時のみ）
