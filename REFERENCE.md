# REFERENCE: Slide PDF スキル詳細リファレンス

スライド生成に使うテンプレート、構成パターン、スタイル詳細をまとめたリファレンス。
`SKILL.md` の補足として必要に応じて参照する。

---

## Marp Markdown テンプレート（フルスタイル付き）

以下をそのまま `/tmp/slide.md` のベースとして使う。スタイルは変更しない。

```markdown
---
marp: true
size: 16:9
style: |
  section {
    position: relative;
    overflow: hidden;
    font-family: "Noto Sans CJK JP", "Noto Sans JP", "Meiryo", sans-serif;
    color: #10324a;
    background: #ffffff;
    padding: calc(54px + 28px) 72px calc(54px + 46px) 72px;
  }
  section h1, section h2, section h3 { color: #0f3652; margin: 0 0 0.35em; }
  section h1 { font-size: 2em; }
  section h2 { font-size: 1.34em; border-left: 8px solid #0aa7ad; padding-left: 0.4em; }
  section p, section li { font-size: 0.94em; line-height: 1.42; }
  section ul, section ol { padding-left: 1.05em; margin: 0.25em 0 0.45em; }
  section li + li { margin-top: 0.18em; }
  section p { margin: 0.2em 0 0.45em; }
  section strong { color: #007e92; }
  section code { background: rgba(13,141,216,0.08); border-radius: 6px; padding: 0.12em 0.35em; }
  section blockquote { margin: 1em 0; padding: 0.5em 0.9em; border-left: 6px solid #0aa7ad; background: rgba(8,180,160,0.08); }
  section table { width: 100%; border-collapse: collapse; background: white; }
  section th, section td { padding: 0.5em 0.7em; border: 1px solid #d8e8ef; }
  section th { background: #eaf8fb; }
  section header, section footer { position: absolute; left: 72px; right: 72px; font-size: 0.58em; }
  section header { top: 18px; }
  section footer { bottom: 18px; }
  section.lead, section.cover {
    color: #ffffff;
    background: linear-gradient(90deg, #0d8dd8 0%, #08b4a0 100%);
  }
  section.lead h1, section.cover h1,
  section.lead h2, section.cover h2,
  section.lead h3, section.cover h3,
  section.lead p, section.cover p,
  section.lead li, section.cover li,
  section.lead strong, section.cover strong,
  section.lead header, section.cover header,
  section.lead footer, section.cover footer { color: #ffffff; }
  section.lead h1, section.cover h1 { margin-top: 0.8em; font-size: 1.9em; line-height: 1.25; max-width: 90%; }
  section.lead p, section.cover p { max-width: 90%; }
  section.lead footer, section.cover footer { position: absolute; left: 72px; right: 72px; bottom: 22px; font-size: 0.52em; color: rgba(255,255,255,0.78); }
  section.lead strong, section.cover strong, section.chapter strong { color: #c8fff1; }
  section.lead code, section.cover code, section.chapter code { color: #ffffff; background: rgba(255,255,255,0.14); }
  section.lead header, section.cover header { position: absolute; top: 42px; left: 72px; display: inline-block; padding: 0.22em 0.6em; color: #0d6078; background: white; border-radius: 4px; font-size: 0.66em; font-weight: 700; letter-spacing: 0.04em; }
  section.lead h1::after, section.cover h1::after { content: ""; display: block; width: 45%; height: 2px; margin-top: 0.45em; background: rgba(255,255,255,0.75); }
  section.chapter {
    color: #ffffff;
    background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0)),
                linear-gradient(90deg, #0f7fca 0%, #0fbea6 100%);
    padding-top: calc(54px + 8px);
    padding-bottom: calc(54px + 28px);
  }
  section.chapter h1, section.chapter h2, section.chapter h3,
  section.chapter p, section.chapter li,
  section.chapter header, section.chapter footer { color: #ffffff; }
  section.chapter h2 { border-left-color: rgba(255,255,255,0.55); }
  section.chapter header, section.chapter footer { color: rgba(255,255,255,0.9); }
  section.chapter h1 { max-width: 90%; }
  section.artifacts-with-image p,
  section.artifacts-with-image ul,
  section.artifacts-with-image ol { max-width: 58%; }
  section.artifacts-with-image .artifacts-shot {
    position: absolute; top: 108px; right: 56px; width: 34%;
    border-radius: 18px; border: 1px solid rgba(16,50,74,0.12);
    box-shadow: 0 14px 30px rgba(16,50,74,0.16);
  }
---

<!-- _class: cover -->

# タイトル
## サブタイトル・日付

---

# スライドタイトル

内容をここに記述。

---
```

---

## スライドクラス一覧

| クラス | 用途 | 背景 |
|--------|------|------|
| `cover` / `lead` | 表紙スライド | 水平グラデーション（青→緑） |
| `chapter` | セクション区切り | 斜めグラデーション（青→緑） |
| なし | 通常コンテンツスライド | 白 |
| `artifacts-with-image` | テキスト＋画像の2カラムレイアウト | 白 |

```markdown
<!-- _class: cover -->      ← 表紙
<!-- _class: chapter -->    ← 章区切り
<!-- _class: artifacts-with-image --> ← 画像付きレイアウト
```

---

## 構成パターン

### 営業・提案資料
```
1. 表紙 (cover)
2. 課題・背景
3. 現状の問題点
4. 解決策の提示
5. [章区切り] (chapter) → 実績・事例
6. 導入実績・数字
7. 提案内容
8. スケジュール・費用
9. 次のアクション (CTA)
```

### 社内報告・定例
```
1. 表紙 (cover)
2. 概要・サマリー
3. [章区切り] (chapter) → 進捗報告
4. KPI・数値進捗
5. 完了タスク
6. [章区切り] (chapter) → 課題・リスク
7. 課題一覧
8. 次アクション
```

### 技術解説・勉強会
```
1. 表紙 (cover)
2. アジェンダ
3. [章区切り] (chapter) → 背景・概念
4-N. 本編スライド（コード例・図解）
N+1. [章区切り] (chapter) → まとめ
N+2. まとめ・参考資料
```

---

## ヘッダー・フッターの使い方

Marp の `_header` / `_footer` ディレクティブでスライドごとに設定できる。

```markdown
<!-- _header: "会社名 | 2024 Q1" -->
<!-- _footer: "Confidential" -->
```

フロントマターで全スライドに適用:

```yaml
header: "会社名 | プレゼン名"
footer: "Confidential — 2024"
```

---

## スライド品質チェックリスト

PDF 生成前に確認:

- [ ] 1スライド1メッセージに絞られているか
- [ ] 表紙スライドに `<!-- _class: cover -->` があるか
- [ ] `font-family` の先頭が `"Noto Sans CJK JP"` になっているか
- [ ] フロントマターに `marp: true` と `size: 16:9` があるか
- [ ] スライド数が多すぎる場合は章ごとに分割を検討（20枚超 → timeout 120）
