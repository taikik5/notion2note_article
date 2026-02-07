# GitHub Actions スケジュール実行 - トラブルシューティング

## ✓ 修正内容

### 1. YAML構文の改善
- `OPENAI_MODEL` のデフォルト値設定を改善（bash の `${var:-default}` 構文を採用）
- エラーハンドリングをより堅牢に

### 2. 秘密情報の検証ステップを追加
- 必須シークレットが設定されているか確認
- 不足している場合は詳細なエラーメッセージを表示

### 3. デバッグログを強化
- 使用している OPENAI_MODEL を明示表示
- ワークフロー完了時のステータスを表示

---

## ⚠️ スケジュール実行が動作しない場合の確認項目

### 1. GitHub Repository Settings の確認

GitHub の Web UI で以下を確認してください：

```
リポジトリ → Settings → Actions → General
```

- [ ] **Actions が有効になっているか**
  - "Disable all" になっていないか確認
  
- [ ] **デフォルトブランチが `main` か確認**
  - スケジュール実行はデフォルトブランチのみで動作

---

### 2. Secrets と variables の確認

```
リポジトリ → Settings → Secrets and variables → Actions
```

以下のシークレットが **すべて** 設定されているか確認：

- [ ] `OPENAI_API_KEY` - OpenAI APIキー
- [ ] `NOTION_TOKEN` - Notion Integration Token  
- [ ] `NOTION_DATABASE_ID_ARTICLE` - Notionデータベース ID
- [ ] `NOTE_STATE_FILE` - (オプション) note.comセッション state (Base64エンコード)

**重要**: シークレットが1つでも不足していると、ワークフローは失敗します。

---

### 3. ワークフロー実行履歴の確認

```
リポジトリ → Actions
```

以下を確認：

- [ ] "Article Auto-Drafter" ワークフローが表示されているか
- [ ] 過去の実行があるか、ないか
- [ ] 失敗している場合、詳細ログを確認
  - クリック → "Verify required secrets are configured" ステップを確認
  - "Run Auto-Drafter" ステップのエラー内容を確認

---

### 4. Cron スケジュール の確認

`.github/workflows/auto-draft.yml` 内の以下の行：

```yaml
schedule:
  - cron: '0 13 * * *'  # 毎日 13:00 UTC（22:00 JST）
```

時刻を変更したい場合：
- [Crontab guru](https://crontab.guru/) で構文を検証
- 変更後、コミットして main ブランチにプッシュ

**注意**: Private リポジトリの場合、スケジュール実行には制限がある可能性があります。

---

### 5. 手動実行でテスト

```
リポジトリ → Actions → Article Auto-Drafter → Run workflow
```

- `workflow_dispatch` トリガーで手動実行可能
- ここで実行できれば、スケジュール実行も動作する可能性が高い

---

## 🔍 ログの見方

### 秘密情報が不足している場合

```
❌ ERROR: Missing required secrets:
  - OPENAI_API_KEY
  - NOTION_DATABASE_ID_ARTICLE
```

→ Settings → Secrets で設定してください

### スクリプト実行時のエラー

```
Using OPENAI_MODEL: gpt-4o-mini
[Step 1] Fetching ready articles from Notion...
Error: NOTION_TOKEN is invalid
```

→ NOTION_TOKEN が正しく設定されているか確認
→ Notion Integration が正しくデータベースに接続されているか確認

---

## 💡 よくある問題と対策

| 問題 | 原因 | 対策 |
|------|------|------|
| ワークフローが表示されない | `.github/workflows/auto-draft.yml` が main ブランチにない | ファイルをプッシュして main ブランチに反映させる |
| スケジュール実行が動作しない | Actions が disabled | Settings → Actions で有効化 |
| "Missing required secrets" エラー | シークレットが設定されていない | Settings → Secrets で設定 |
| "permission denied" エラー | `base64` コマンドが失敗 | `note-state.json` が存在するか確認 |
| スクリプト実行エラー | Playwright のインストール失敗 | ワークフロー実行ログで詳細を確認 |

---

## 📝 最後の確認チェックリスト

- [ ] `.github/workflows/auto-draft.yml` が main ブランチにプッシュされている
- [ ] Repository Settings → Actions が有効
- [ ] Secrets がすべて設定されている
- [ ] 手動実行 (`workflow_dispatch`) でテストした
- [ ] ワークフロー実行ログで特定のエラーが見つかった場合、上記の対策を実施

---

## ℹ️ その他の参考資料

- [GitHub Actions スケジュール実行の公式ドキュメント](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)
- [GitHub Actions の Secrets について](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)
- [Crontab guru - Cron スケジュール検証ツール](https://crontab.guru/)
