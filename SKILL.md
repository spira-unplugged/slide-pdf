---
name: slide-pdf
description: Generate PDF slide decks from Markdown using Marp. Use this skill whenever the user wants to create a presentation, make slides, build a slide deck, convert Marp Markdown to PDF, or generate any kind of slides or presentation materials. Also use when the user uploads a .md file intended as slides.
dependencies: "@marp-team/marp-cli>=3.0.0"
---

# Slide PDF

Marp CLI + Playwright Chromium で Markdown スライドを PDF に変換するスキル。

## 実行方法

`generate.py` スクリプトを使う。直接 bash コマンドより確実にエラー処理・タイムアウト自動算出・スタイル注入が行われる。

```bash
python /path/to/skill/generate.py --input /tmp/slide.md --output /mnt/user-data/outputs/slides.pdf
```

手動でコマンドを組む場合（generate.py が使えない環境）:

```bash
SLIDE_COUNT=$(grep -c '^---$' /tmp/slide.md || echo 10)
TIMEOUT=$(( SLIDE_COUNT > 20 ? 120 : 60 ))
timeout $TIMEOUT npx @marp-team/marp-cli /tmp/slide.md \
  --no-stdin --pdf \
  --browser chrome \
  --browser-path /opt/pw-browsers/chromium-1194/chrome-linux/chrome \
  -o /mnt/user-data/outputs/slides.pdf
```

## フロー

### パターンA: ユーザーが Marp Markdown をアップロードした場合

1. `/mnt/user-data/uploads/` のファイルを `/tmp/slide.md` にコピー
2. `generate.py` を実行（スタイルが未定義なら自動注入される）
3. `present_files` で PDF を渡す

### パターンB: お題・テキストからゼロ生成する場合

1. **スライド構成を決める**（REFERENCE.md の構成パターンを参照）
2. **Markdown を生成して `/tmp/slide.md` に保存**（REFERENCE.md のテンプレートを使う）
3. `generate.py` を実行
4. `present_files` で PDF を渡す

スライドクラスの使い分け:
- `<!-- _class: cover -->`: 表紙スライド（グラデーション背景）
- `<!-- _class: chapter -->`: セクション区切り（グラデーション背景）
- クラス指定なし: 通常スライド（白背景）

## エラーハンドリング

| エラー | 原因 | 対処 |
|--------|------|------|
| exit code 124 | タイムアウト | スライド枚数が多い。`timeout 120` で再実行 |
| PDF が真っ白 | wkhtmltopdf が混入 | 必ず Marp CLI + Chromium を使う |
| 日本語が豆腐 | フォント未適用 | `font-family` の先頭が `"Noto Sans CJK JP"` か確認 |
| その他 | — | stderr ログをそのままユーザーに報告 |

## 注意事項

- **フォント**: `font-family` は必ず `"Noto Sans CJK JP"` を先頭に置く（`"Noto Sans JP"` だけだと簡体字になる環境がある）
- **テーマ指定**: `--theme` は使わない。CSS はフロントマターの `style:` にインライン定義
- **wkhtmltopdf 禁止**: Marp は JS ベース SVG 構造のため wkhtmltopdf では真っ白になる

詳細な CSS テンプレートと構成パターンは `REFERENCE.md` を参照。
