# DBの設計について
デバイスから取得された以下の形式のデータからDBの設計を行う。

## 作成するDBの構造
'''database/docs/DB_abstract.png''' の構造に従う。
DBには、postgresqlを使用する。

## データの取得について
- 収集した基本データは以下のスプレッドシートからデータを定期的に取得する。
https://docs.google.com/spreadsheets/d/1LUE3KlT_J1lSgYmclg-ljiXDS4JYaAwEtc0X-ia-twU/edit?usp=sharing
- 収集した基本データに加えて、その時刻の天候状況をAPIを使って取得・追加する。
- 場所は静岡県浜松市中央区とする。


## git上での作業について
feature/DB ブランチ内で作業を行い、動作確認・CI/CD が完了したらmainにマージ・pushする。

# 注意事項全般
- 作業に取り掛かる前に、適切なディレクトリ構造を提案してから、作業を開始してください。
- 作業の進捗に応じて、適宜、このファイルを修正してください。

# このファイルはgit上へアップロードすることを禁ずる。