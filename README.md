# AI開発ダイジェスト

毎朝（平日 7:00 JST）、AI開発ツール関連のRSSフィードを集めて日本語で要約したダイジェストを GitHub Pages に自動公開する仕組み。スマホのブラウザで `https://<user>.github.io/<repo>/` を開くと最新版が見られる。

## 仕組み

```
Claude Code scheduled-task (平日 07:00)
   │
   ├─ python scripts/fetch_feeds.py   ← RSS を並列取得して data/raw_<date>.json
   ├─ Claude が関連性評価 + 日本語要約 + HTML生成
   └─ git push → GitHub Pages 自動デプロイ
```

- **実行マニュアル**: [CLAUDE.md](./CLAUDE.md) — scheduled-task がこれを読んで毎朝走る
- **フィード一覧**: [feeds.yaml](./feeds.yaml) — 追加/削除はここを編集
- **テンプレート**: [templates/](./templates/) — HTMLとCSS（モバイルファースト）

## ディレクトリ

```
news/
├── CLAUDE.md              毎朝の実行手順（scheduled-task が参照）
├── feeds.yaml             RSSフィード一覧
├── scripts/
│   └── fetch_feeds.py     RSSフェッチスクリプト
├── templates/
│   ├── digest.html        ダイジェストのHTMLテンプレ
│   └── style.css          モバイルファーストCSS
├── data/                  フェッチ結果キャッシュ（.gitignore）
└── docs/                  GitHub Pages 公開ルート
    ├── index.html         最新ダイジェスト（毎朝上書き）
    ├── style.css
    └── archive/
        ├── index.html     過去一覧
        └── YYYY-MM-DD.html 日付ごと
```

## セットアップ（初回のみ）

### 1. Python 依存インストール
```
pip install feedparser pyyaml
```

### 2. フェッチ動作確認
```
python scripts/fetch_feeds.py
```
`data/raw_<today>.json` が生成され、各フィードの件数ログが出ればOK。

### 3. GitHub リポジトリ準備
- GitHub でリポジトリを作成（例: `news-digest`、public）
- ローカルで初期化してプッシュ
  ```
  git init
  git add .
  git commit -m "initial setup"
  git branch -M main
  git remote add origin https://github.com/<user>/<repo>.git
  git push -u origin main
  ```

### 4. GitHub Pages を有効化
リポジトリの Settings → Pages:
- Source: `Deploy from a branch`
- Branch: `main` / folder: `/docs`

数分で `https://<user>.github.io/<repo>/` が公開される。

### 5. scheduled-task を登録
Claude Code で:
```
mcp__scheduled-tasks__create_scheduled_task を
  taskId: morning-ai-digest
  cronExpression: 0 7 * * 1-5
  prompt: "プロジェクトディレクトリ C:\\Users\\81801\\OneDrive\\デスクトップ\\Claude Code\\news の CLAUDE.md に従ってダイジェストを生成・公開してください"
  description: 平日朝7時のAI開発ツールダイジェスト生成
で呼び出す
```

## スマホでの利用

1. iOS/Android のブラウザで公開 URL を開く
2. ホーム画面に追加（iOS: 共有 → ホーム画面に追加 / Android: メニュー → ホーム画面に追加）
3. 毎朝そのアイコンから最新ダイジェストを開くだけ

## フィードの追加・削除

`feeds.yaml` を編集してコミットするだけ。次回の実行から反映される。

## 手動実行

scheduled-task を待たずに今すぐ生成したい場合は、Claude Code で:
> `CLAUDE.md` に従って今日のダイジェストを生成して
