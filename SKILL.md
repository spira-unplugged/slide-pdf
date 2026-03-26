---
name: slide-pdf
description: Create slide decks from Markdown as PDF/PPTX/HTML using Marp. Use whenever the user wants slides, a presentation, or a pitch deck, or uploads a .md file. Use even if not explicitly asked.
dependencies: "@marp-team/marp-cli>=3.0.0"
---

# Slide PDF

Marp CLI + Playwright Chromium で Markdown スライドを PDF / PPTX / HTML に変換するスキル。

## 実行方法

`generate.py` スクリプトを使う。エラー処理・タイムアウト自動算出・スタイル注入・フォーマット変換が自動で行われる。

```bash
# PDF（デフォルト）
python /path/to/skill/generate.py --input /tmp/slide.md

# PowerPoint（PPTX）
python /path/to/skill/generate.py --input /tmp/slide.md --format pptx

# HTML スライド
python /path/to/skill/generate.py --input /tmp/slide.md --format html

# gaia テーマで PDF
python /path/to/skill/generate.py --input /tmp/slide.md --theme gaia

# 数式あり（MathJax）
python /path/to/skill/generate.py --input /tmp/slide.md --math mathjax

# スピーカーノート付き PDF
python /path/to/skill/generate.py --input /tmp/slide.md --pdf-notes
```

## フラグ一覧

| フラグ | 値 | デフォルト | 説明 |
|--------|----|-----------|------|
| `--format` | `pdf` / `pptx` / `html` | `pdf` | 出力フォーマット |
| `--theme` | `default` / `gaia` / `uncover` | `default` | Marp テーマ |
| `--size` | `16:9` / `4:3` / `9:16` | `16:9` | スライドのアスペクト比 |
| `--pdf-outlines` | （フラグ） | 自動（5枚超で有効） | PDF しおり（ブックマーク）を追加 |
| `--pdf-notes` | （フラグ） | なし | スピーカーノートを PDF に含める |
| `--math` | `mathjax` / `katex` / `none` | `none` | 数式レンダリングエンジン |
| `--lint` | （フラグ） | なし | Marp CLI を起動せずスライド構造を検証（終了コード 0=OK / 1=問題あり） |
| `--json` | （フラグ） | なし | 処理結果を JSON で stdout に出力（AI 統合用） |

## フォーマット・テーマの選び方

### フォーマット
- **PDF**（デフォルト）: 配布・印刷用。`--pdf-outlines` は5枚超で自動有効。
- **PPTX**: ユーザーが「PowerPoint で出力」「編集できる形式で」と言ったとき。
- **HTML**: ユーザーが「HTML スライドで」「ブラウザで見たい」と言ったとき。

### テーマ
- **default**（デフォルト）: カスタム CSS（Noto Sans CJK JP / グラデーション）を自動注入。日本語・コーポレート向け。
- **gaia**: Marp 組み込みミニマリストテーマ。シンプルな発表資料向け。カスタム CSS は注入しない。
- **uncover**: Marp 組み込みプレゼンテーションテーマ。白背景・洗練されたレイアウト。カスタム CSS は注入しない。

> **注意**: `--theme gaia` / `--theme uncover` を使う場合はカスタム `style:` を追加しない。

### 数式
- ユーザーのスライド内容に数式・方程式・科学技術系の数式表記が含まれる場合は `--math mathjax` を渡す。
- KaTeX を明示的に要求された場合のみ `--math katex` を使う。

## フロー

### パターンA: ユーザーが Marp Markdown をアップロードした場合

1. `/mnt/user-data/uploads/` のファイルを `/tmp/slide.md` にコピー
2. `generate.py` を実行（スタイルが未定義なら自動注入される）
3. `present_files` で出力ファイルを渡す

### パターンB: お題・テキストからゼロ生成する場合

1. **スライド構成を決める**（REFERENCE.md の構成パターンを参照）
2. **Markdown を生成して `/tmp/slide.md` に保存**（REFERENCE.md のテンプレートを使う）
3. `generate.py` を実行（適切なフラグを付ける）
4. `present_files` で出力ファイルを渡す

スライドクラスの使い分け:
- `<!-- _class: cover -->`: 表紙スライド（グラデーション背景）
- `<!-- _class: chapter -->`: セクション区切り（グラデーション背景）
- クラス指定なし: 通常スライド（白背景）

## エラーハンドリング

| エラー | 原因 | 対処 |
|--------|------|------|
| exit code 124 | タイムアウト | スライド枚数が多い。枚数を減らすか複数ファイルに分割 |
| PDF が真っ白 | wkhtmltopdf が混入 | 必ず Marp CLI + Chromium を使う |
| 日本語が豆腐 | フォント未適用 | `font-family` の先頭が `"Noto Sans CJK JP"` か確認 |
| Chromium not found | Chromium 未インストール | `CHROMIUM_PATH` 環境変数でパスを明示する |
| その他 | — | stderr ログをそのままユーザーに報告 |

## 注意事項

- **フォント**: `font-family` は必ず `"Noto Sans CJK JP"` を先頭に置く（`"Noto Sans JP"` だけだと簡体字になる環境がある）
- **テーマ + スタイル**: `--theme gaia` / `--theme uncover` を指定した場合はカスタム CSS を注入しない（テーマが自前の CSS を持つ）
- **wkhtmltopdf 禁止**: Marp は JS ベース SVG 構造のため wkhtmltopdf では真っ白になる
- **数式**: `math: mathjax` は Marp CLI に同梱。追加インストール不要。

詳細な CSS テンプレートと構成パターンは `REFERENCE.md` を参照。
