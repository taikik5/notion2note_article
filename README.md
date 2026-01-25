# notion2note_article

Notionに記事のネタを書き込むと、AIが自動で記事を生成し、note.comの下書きに投稿するシステムです。

## 概要

このツールは以下の処理を自動で行います：

1. **Notionからデータ取得** - `Status=Ready` の記事を取得
2. **AI記事生成** - モードに応じたプロンプトで文章を生成（OpenAI API使用）
3. **ヘッダー画像生成** - 記事タイトルを画像に描画
4. **note.com投稿** - 下書きとして自動保存
5. **Notion更新** - ステータスを `Done` に変更

### 3つのモード

| モード | 用途 | 特徴 |
|--------|------|------|
| **共感・エッセイ型** | 体験談、意見、日記的な内容 | 親しみやすい語り口、失敗談、問いかけ表現 |
| **ノウハウ・ビジネス型** | 仕事術、ライフハック、ツール紹介 | 結論ファースト、箇条書き、具体的なアクション |
| **推敲・リライト型** | 既存の下書きをブラッシュアップ | 読みやすさ改善、フック強化、リズム創出 |

---

## フォルダ構成

```
notion2note_article/
├── src/                           # メインソースコード
│   ├── main.py                    # メインオーケストレーター
│   ├── notion_client_module.py    # Notion API連携
│   ├── openai_formatter.py        # OpenAI文章生成
│   ├── note_automation.py         # note.com投稿自動化
│   ├── image_generator.py         # ヘッダー画像生成
│   └── prompts/                   # モード別プロンプト
│       ├── base.py                # 共通マークダウンルール
│       ├── empathy_essay.py       # 共感・エッセイ型
│       ├── knowhow_business.py    # ノウハウ・ビジネス型
│       └── rewrite.py             # 推敲・リライト型
├── assets/                        # 静的リソース
│   └── header_background.png      # ヘッダー画像の背景
├── .github/workflows/
│   └── auto-draft.yml             # GitHub Actions定義
├── login-note.js                  # note.comログインスクリプト
├── requirements.txt               # Python依存パッケージ
├── package.json                   # Node.js依存パッケージ
├── .env.example                   # 環境変数テンプレート
└── README.md                      # このファイル
```

---

## 事前準備

### 1. 必要なアカウント・APIキー

以下を事前に取得してください：

| 項目 | 取得方法 |
|------|----------|
| **OpenAI APIキー** | [OpenAI Platform](https://platform.openai.com/api-keys) でAPIキーを発行 |
| **Notion Integration Token** | [Notion Developers](https://www.notion.so/my-integrations) でインテグレーションを作成 |
| **note.comアカウント** | [note.com](https://note.com/) でアカウント作成 |

### 2. Notionデータベースの作成

Notionで新しいデータベースを作成し、以下のプロパティを設定してください：

| プロパティ名 | タイプ | 設定内容 |
|-------------|--------|----------|
| **ID** | 番号 または ID | 自動採番される行番号（自動採番する設定にする）※unique_id型にも対応 |
| **モード** | セレクト または マルチセレクト | 以下の3つのオプションを作成：<br>・`共感・エッセイ型`<br>・`ノウハウ・ビジネス型`<br>・`推敲・リライト型` |
| **文章のネタ** | テキスト | 記事の素材（長文可）※`テキスト`、`Content`でも可 |
| **Status** | ステータス | `Ready` と `Done` を作成 |

> **補足：プロパティ名の柔軟性**
>
> コードは以下のプロパティ名にも対応しています：
> - ID列: `ID`（番号型・unique_id型両対応）、`タイトル`、`Title`、`name`
> - コンテンツ列: `文章のネタ`、`テキスト`、`Content`、`content`

### 3. Notionインテグレーションの接続

1. 作成したデータベースを開く
2. 右上の `...` メニュー → `接続` → 作成したインテグレーションを選択
3. データベースURLから **Database ID** を取得（URLの末尾32文字）

```
https://www.notion.so/xxxxxxxx?v=yyyyyyyy
                      ^^^^^^^^
                      この部分がDatabase ID
```

---

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd notion2note_article
```

### 2. Python仮想環境の作成と有効化

```bash
# 仮想環境を作成
python -m venv venv

# 仮想環境を有効化
# macOS/Linux:
source venv/bin/activate

# Windows:
.\venv\Scripts\activate
```

### 3. Python依存パッケージのインストール

```bash
pip install -r requirements.txt

# Playwrightブラウザのインストール
# このステップは重要です。スキップしないでください。
pip install playwright
playwright install chromium
```

> **注意：Playwrightが見つからないエラーが出た場合**
>
> もし `npm run login` を実行した時に以下のエラーが出た場合：
> ```
> browserType.launch: Executable doesn't exist at /Users/taiki/Library/Caches/ms-playwright/chromium-1208/...
> Please run the following command to download new browsers:
> npx playwright install
> ```
>
> 以下を実行してください：
> ```bash
> npx playwright install
> ```

### 4. Node.js依存パッケージのインストール

```bash
npm install

# Node.js用のPlaywrightブラウザもインストール（login-note.js用）
npx playwright install chromium
```

### 5. 環境変数の設定

```bash
# テンプレートをコピー
cp .env.example .env

# .envファイルを編集して値を設定
```

`.env` ファイルの内容：

```ini
# OpenAI API Key
OPENAI_API_KEY=sk-xxxxx

# OpenAI Model（省略可、デフォルト: gpt-4o-mini）
OPENAI_MODEL=gpt-4o-mini

# Notion Integration Token
NOTION_TOKEN=secret_xxxxx

# Notion Database ID
NOTION_DATABASE_ID=xxxxx
```

### 6. note.comへのログイン（セッション保存）

```bash
npm run login
```

ブラウザが開くので、手動でnote.comにログインしてください。
ログイン完了後、セッション情報が `note-state.json` に保存されます。

---

## 使い方

### ローカル実行

```bash
# 仮想環境が有効化されていることを確認
source venv/bin/activate  # macOS/Linux
# または
.\venv\Scripts\activate   # Windows

# 実行
python src/main.py
```

### 動作フロー

1. Notionデータベースで記事を作成
2. `モード` を選択（共感・エッセイ型 など）
3. `文章のネタ` に素材を入力
4. `Status` を `Ready` に設定
5. `python src/main.py` を実行
6. note.comの下書きに記事が投稿される
7. Notionの `Status` が自動で `Done` に更新

---

## GitHub Actionsでの自動実行

毎日自動で実行したい場合は、GitHub Actionsを設定します。

### 必要なSecrets

リポジトリの `Settings` → `Secrets and variables` → `Actions` で以下を設定：

| Secret名 | 値 |
|----------|-----|
| `OPENAI_API_KEY` | OpenAI APIキー |
| `NOTION_TOKEN` | Notion Integration Token |
| `NOTION_DATABASE_ID_ARTICLE` | NotionデータベースID |
| `NOTE_STATE_FILE` | `note-state.json` をBase64エンコードした値 |

### note-state.jsonのBase64エンコード

```bash
# macOS/Linux
cat note-state.json | base64 | pbcopy
# クリップボードにコピーされるので、Secretsに貼り付け

# または
cat note-state.json | base64
# 出力をコピーしてSecretsに貼り付け
```

### 実行スケジュール

デフォルトでは毎日22:00 JST（13:00 UTC）に実行されます。
変更する場合は `.github/workflows/auto-draft.yml` の `cron` を編集してください。

---

## トラブルシューティング

### Playwrightブラウザが見つからないエラー

```
browserType.launch: Executable doesn't exist at /Users/taiki/Library/Caches/ms-playwright/...
Please run the following command to download new browsers:
npx playwright install
```

**原因：** Playwrightのブラウザドライバがインストールされていない

**解決方法：**
```bash
# Python用
playwright install chromium

# または Node.js用
npx playwright install chromium
```

セットアップ手順の「3. Python依存パッケージのインストール」と「4. Node.js依存パッケージのインストール」で実行されるはずですが、スキップされた場合は上記を実行してください。

### 記事が処理されない（Warning: Empty content エラー）

```
Warning: Empty content (文章のネタ), skipping.
```

**原因：** Notionから記事コンテンツが正しく取得できていない

**確認項目：**
1. Notionのプロパティ名がコードの期待値と一致しているか確認：
   - `ID` （番号型 または unique_id型）
   - `モード` （セレクト型 または マルチセレクト型）
   - `文章のネタ`、`テキスト`、`Content` のいずれか（テキスト型）
   - `Status` （ステータス型）
2. 記事のテキスト欄に内容が入力されているか確認
3. 記事の `Status` が `Ready` に設定されているか確認
4. Notionインテグレーションがデータベースに接続されているか確認

### セッション切れエラー

```
Session expired or invalid. Redirected to login page.
```

→ `npm run login` を再実行してセッションを更新してください。

### note.comへの投稿が失敗する

1. `note-state.json` が存在するか確認
2. セッションが有効か確認（`npm run login` で再取得）
3. スクリーンショット（`error_screenshot.png`）を確認

### 日本語フォントが表示されない

GitHub Actionsで日本語フォントがない場合、グラデーション背景にフォールバックされます。
日本語フォント（NotoSansJP-Bold.ttf など）を `assets/` フォルダに配置すると改善します。

---

## 依存関係

### Python

- `notion-client` - Notion API
- `openai` - OpenAI API
- `playwright` - ブラウザ自動化
- `Pillow` - 画像生成
- `python-dotenv` - 環境変数管理

### Node.js

- `playwright` - note.comログイン用

---

## 技術詳細

### 対応するNotionプロパティ型

このツールは以下のNotionプロパティ型に対応しています：

| プロパティ | 対応する型 |
|-----------|-----------|
| ID | `number`、`unique_id`、`title` |
| モード | `select`、`multi_select` |
| 文章のネタ | `rich_text` |
| Status | `status` |

### OpenAIモデル

デフォルトでは `gpt-4o-mini` を使用します。`.env` ファイルの `OPENAI_MODEL` で変更可能です。

---

## ライセンス

MIT License
