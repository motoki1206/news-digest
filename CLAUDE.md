# 毎朝のダイジェスト生成手順

このファイルは **scheduled-task が毎朝 Claude Code に読ませる実行マニュアル**。
ここに書かれた手順を上から順に実行してダイジェストを生成・公開する。

プロジェクトルート: `C:\Users\81801\OneDrive\デスクトップ\Claude Code\news`
公開URL: GitHub Pages（リポジトリの `/docs` を公開ルートに設定済み）

---

## 毎朝の実行フロー

### 1. 作業ディレクトリへ移動
```
cd "C:/Users/81801/OneDrive/デスクトップ/Claude Code/news"
```

### 2. RSS フィードを取得
```
python scripts/fetch_feeds.py
```
- `data/raw_YYYY-MM-DD.json` が生成される
- 各フィードの件数・エラーが標準出力に出る
- 1フィード失敗しても続行する設計。errors 配列を後で軽く確認するだけで良い

### 3. 取得結果を読む
`data/raw_<today>.json` を Read する。`items` 配列には `{source, category, title, url, published_at, summary, tags}` が新しい順で入っている。

### 4. 関連性評価と選定（最重要）
以下の方針で **12〜18 件程度** に絞る。多すぎても読まれない、少なすぎても物足りない。

**ピックアップの基準**:
- Claude / Claude Code / Anthropic 関連の公式発表・アップデートは優先度最高
- AI開発ツール（Cursor, GitHub Copilot, Codex, Windsurf, Cline 等）のアップデートや比較記事
- 実際の使いこなしTips、ワークフロー、プロンプト工夫などユーザー視点で有用な記事
- ノイズは除外: 単なる宣伝、内容の薄い告知、AI でない一般テック記事、同じ話題の重複

**セクション分類**（テンプレートのコメント参照）:
- 📣 トップピック: 上位3件。その日最も読む価値のあるもの。`class="pick"` を付け、`<div class="pick-note">` に選定理由を1行で添える
- 🤖 Claude / Anthropic: Anthropic公式・Claude関連
- 🛠️ AI開発ツール: 他社AIコーディングツール、エディタ連携
- 📚 技術Tips・事例: Zenn / Qiita / HN の実践的な記事

### 5. HTML を生成

テンプレートは `templates/digest.html`。プレースホルダ:
- `{{DATE}}` → `2026-04-16`
- `{{DATE_LABEL}}` → `2026年4月16日 (木)`
- `{{LEDE}}` → その日のハイライトを 1〜2 文で要約（「本日は Claude Code の新バージョンリリースと…」など）
- `{{CONTENT}}` → 各セクション + 記事の HTML
- `{{GENERATED_AT}}` → `2026-04-16 07:05 JST`

**記事ひとつのHTML**（要約は日本語で 2〜3 行、読者が元記事を開くかどうか判断できる密度に）:
```html
<article class="item">
  <h3><a href="URL" target="_blank" rel="noopener">タイトル</a></h3>
  <div class="meta"><span class="source">元サイト名</span><span>MM/DD HH:mm</span></div>
  <p class="body">日本語要約。何についての記事で、何が新しいか、なぜ読む価値があるかを2〜3文で。</p>
</article>
```

トップピックのみ:
```html
<article class="item pick">
  <div class="pick-note">▶ 選定理由を1行</div>
  <h3>...</h3>
  ...
</article>
```

必要なら重要記事は `WebFetch` で元ページを取って要約精度を上げる（**目安: トップピック3件のみ**、全件やるとコストが膨らむ）。

### 6. 出力ファイルを書く

- `docs/archive/YYYY-MM-DD.html` を新規作成（その日の固定URL）
- `docs/index.html` を **同じ内容で上書き**（スマホのブックマーク先を最新に保つため）
- `docs/style.css` が無ければ `templates/style.css` をコピー

### 7. アーカイブ一覧を更新

`docs/archive/index.html` の `<ul class="archive-list">` 先頭に今日のエントリを追加:
```html
<li><a href="./YYYY-MM-DD.html"><span>YYYY年MM月DD日 (曜)</span><span>見出し一言</span></a></li>
```
90日より古いエントリは削除して OK（ファイルはアーカイブディレクトリに残したままで一覧からだけ外す）。

### 8. git コミット & プッシュ
```
git add docs/
git commit -m "digest: YYYY-MM-DD"
git push
```
GitHub Pages は push から 1〜2 分で反映される。

### 9. 完了報告

- 取得件数 / 選定件数 / エラーがあれば件名
- 公開URL（ブックマーク用にコピペしやすく）
- 今日のトップピック 3 件の見出しだけ

---

## トラブルシューティング

- **python not found**: `py scripts/fetch_feeds.py` で代替
- **feedparser / yaml import error**: `pip install feedparser pyyaml`
- **全フィードが空**: ネット不通 or feeds.yaml の URL が全滅。errors を確認して前日の `index.html` はそのままに、失敗を報告して終了（無理に空のダイジェストを出さない）
- **git push が失敗**: 認証切れの可能性。`gh auth status` を確認してユーザーに報告
- **GitHub Pages に反映されない**: Settings → Pages で Source が `main` の `/docs` になっているか確認
