---
id: p_20261001_180039_614d1b
status: pending
title: mdファイルのレポート作成ルール
source: 00_Journal/how-to-write.md
suggested_path: report/writing_rules.md
created: 2026-10-01T18:00:39.624892
---

# mdファイルのレポート作成ルール

レポートファイルは本ディレクトリ内の`posts`に格納し、ファイル名は`yyyymmddHHMMSS_title.md`で統一。日本語文字は使用しない。

ファイル内に記入する必須事項は以下の通り。
- `<!--mote-->`以前の内容がリストに表示される。
- 文頭に、date、categories、title、概要文を指定する。
- categoriesは以前に使用したカテゴリを基本とし、不足した場合に新規で追加。
- dateのcreatedとupdatedフィールドは、内容を追記した際に日付を更新する。

## REIからの提案理由

mdファイルのレポート作成ルールは、プロジェクトの標準的なファイル構造と命名規則を明確にし、後続の作業で再利用可能な基準を提供する。このルールは、ファイル管理の一貫性を保ち、チームメンバー間の理解を促進するための長期的な価値を持つ。
