# EVAL DEFINITION: slide-pdf

スキルの品質を担保する評価定義。EDD（Eval-Driven Development）に従い、
実装変更のたびにこの定義に照らして評価を実行する。

---

## Capability Evals（スキル能動的呼び出し）

Claude がスキルを正しくトリガーし、適切な出力を生成できるか検証する。

### CE-1: 日本語プロンプトからのゼロ生成
**Prompt**: 「会社紹介のスライドを10枚作って」
**Success Criteria**:
- [ ] `marp: true` が frontmatter に含まれる
- [ ] `size: 16:9` が含まれる
- [ ] `style:` ブロックが含まれる
- [ ] `font-family` に `"Noto Sans CJK JP"` が含まれる
- [ ] `<!-- _class: cover -->` の表紙スライドがある
- [ ] スライドが `---` で区切られ複数枚ある
- [ ] generate.py または PDF生成コマンドが実行される
- [ ] `present_files` で PDF が渡される

**Grader**: Model grader（Markdown出力の構造検査）+ Code grader（generate.py 実行確認）

---

### CE-2: 英語プロンプトからの生成
**Prompt**: "Create a 5-slide pitch deck for a SaaS product"
**Success Criteria**:
- [ ] Marp frontmatter が正しく出力される
- [ ] カバースライドに `<!-- _class: cover -->` がある
- [ ] 5枚前後のスライドが生成される
- [ ] PDF生成フローが実行される

**Grader**: Model grader

---

### CE-3: アップロードファイルの変換（スタイルなし）
**Prompt**: 「このMarkdownをスライドにして（style:なしのファイル）」
**Input file** (`/mnt/user-data/uploads/test.md`):
```markdown
---
marp: true
size: 16:9
---
# タイトル
---
# スライド2
- 内容
```
**Success Criteria**:
- [ ] `style:` ブロックが自動注入される
- [ ] `font-family: "Noto Sans CJK JP"` が含まれる
- [ ] PDF が生成される

**Grader**: Code grader（inject_style の出力検査）

---

### CE-4: アップロードファイルの変換（スタイルあり）
**Prompt**: 「このMarpファイルをPDFにして（style:あり）」
**Success Criteria**:
- [ ] 既存の `style:` が上書きされない
- [ ] PDF が生成される

**Grader**: Code grader

---

## Regression Evals（非トリガー確認）

スキルが呼ばれるべきでない場面で誤トリガーしないか検証する。

### RE-1: PDF読み込み（スライドではない）
**Prompt**: 「このPDFの内容を要約して」
**Expected**: slide-pdf スキルは呼ばれない

### RE-2: 画像変換
**Prompt**: 「この画像をPNGに変換して」
**Expected**: slide-pdf スキルは呼ばれない

### RE-3: コード解説
**Prompt**: 「この Python コードを説明して」
**Expected**: slide-pdf スキルは呼ばれない

---

## generate.py Unit Evals（コードベースグレーダー）

`evals/grade.py` を実行することで自動検証する。

### UE-1: count_slides — 基本カウント
**Input**: `---` が3回（frontmatter終了 + スライド区切り2回）
**Expected output**: `2`

### UE-2: count_slides — フロントマターのみ
**Input**: frontmatter の `---` のみ
**Expected output**: `1`（最低1として扱う）

### UE-3: has_style_block — スタイルあり
**Input**: frontmatter に `style: |` を含む Markdown
**Expected output**: `True`

### UE-4: has_style_block — スタイルなし
**Input**: frontmatter に `style:` を含まない Markdown
**Expected output**: `False`

### UE-5: inject_style — 注入後にスタイルが含まれる
**Input**: スタイルなしの Marp Markdown
**Expected output**: `style:` + `"Noto Sans CJK JP"` が含まれる

### UE-6: inject_style — フロントマターなしの場合
**Input**: フロントマターのない素の Markdown
**Expected output**: `marp: true` + `style:` が先頭に追加される

### UE-7: inject_style — 既存スタイルを上書きしない
**Input**: すでに `style:` を持つ Markdown（UE-3と同じ）
**Expected output**: 元のコンテンツと同一（inject されない）

---

## Success Metrics

| カテゴリ | 目標 |
|----------|------|
| Capability Evals | pass@3 ≥ 90% |
| Regression Evals | pass^3 = 100% |
| Unit Evals | pass@1 = 100% |

---

## 実行方法

```bash
# Unit Evals（自動）
python evals/grade.py

# Capability / Regression Evals（手動 or モデルグレーダー）
# Claude に上記プロンプトを送り、出力を SUCCESS CRITERIA と照合する
```

## Eval Run Log

| Date | CE-1 | CE-2 | CE-3 | CE-4 | RE-1 | RE-2 | RE-3 | UE 1-7 |
|------|------|------|------|------|------|------|------|---------|
| — | — | — | — | — | — | — | — | — |
