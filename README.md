# slide-pdf

Claude Skill: Markdown → PDF / PPTX / HTML スライド生成（Marp CLI + Chromium）

## 何ができるか

- テーマ・構成を指示するだけで Marp Markdown スライドをゼロから生成し PDF / PPTX / HTML で出力
- アップロードした `.md` ファイルを PDF に変換（`style:` がなければ自動注入）
- 日本語対応（Noto Sans CJK JP フォント使用）
- Marp 組み込みテーマ対応（`default` / `gaia` / `uncover`）
- アスペクト比選択（`16:9` / `4:3` / `9:16`）
- 数式レンダリング対応（MathJax / KaTeX）
- PDF しおり自動追加（5枚超で有効）・スピーカーノート PDF 出力
- `--lint` でスライド構造を事前検証（Marp CLI 起動なし）
- `--json` で処理結果を構造化 JSON 出力（AI 統合用）

## インストール

### Claude.ai（推奨）

1. このリポジトリを ZIP でダウンロード
2. Claude.ai → **Customize > Skills** → **Upload Skill** で ZIP をアップロード
3. スキルを有効化

### Claude Code

```bash
# リポジトリごとクローンしてスキルとして登録
git clone https://github.com/spira-unplugged/slide-pdf
```

`~/.claude/skills/slide-pdf/` に配置することで Claude Code から参照可能。

## 使い方

### スライドをゼロから作る

```
会社紹介のプレゼン資料を10枚作って
```

```
SaaS製品の営業用ピッチデッキを作って（英語）
```

```
gaiaテーマで製品ロードマップのスライドを作って
```

```
二次方程式の解説スライドを数式付きで作って
```

### アップロードファイルを PDF に変換

Marp Markdown ファイル（`.md`）をアップロードして:

```
このMarkdownをPDFスライドにして
```

```
このMarkdownをPowerPointで出力して
```

## 技術構成

| コンポーネント | 詳細 |
|--------------|------|
| スライドエンジン | [Marp CLI](https://github.com/marp-team/marp-cli) |
| PDF レンダリング | Playwright 同梱 Chromium |
| フォント | Noto Sans CJK JP（日本語優先） |
| 出力フォーマット | PDF / PPTX / HTML |
| テーマ | default（カスタム CSS）/ gaia / uncover |
| 数式 | MathJax / KaTeX（Marp CLI 同梱） |
| 出力先 | `/mnt/user-data/outputs/slides.<format>` |

## スライドクラス

| クラス | 用途 |
|--------|------|
| `cover` / `lead` | 表紙（グラデーション背景） |
| `chapter` | セクション区切り（グラデーション背景） |
| なし | 通常コンテンツ（白背景） |

## ファイル構成

```
slide-pdf/
├── SKILL.md          # スキル定義（Claude が読む）
├── generate.py       # PDF 生成スクリプト
├── REFERENCE.md      # CSS テンプレート・構成パターン詳細
└── evals/
    ├── evals.json    # eval 定義（19 ケース）
    └── grade.py      # Unit eval 自動グレーダー（31 ケース）
```

## Eval の実行

Unit eval（`generate.py` の純粋関数を自動検証）:

```bash
python evals/grade.py
# 期待結果: 31/31 passed
```

## 環境変数

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `CHROMIUM_PATH` | `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` | Chromium バイナリのパス |
| `ALLOWED_INPUT_BASE` | `/mnt/user-data` | 入力ファイルの許可ベースディレクトリ |
| `ALLOWED_OUTPUT_BASE` | `/mnt/user-data/outputs` | 出力ファイルの許可ベースディレクトリ |

## ライセンス

MIT
