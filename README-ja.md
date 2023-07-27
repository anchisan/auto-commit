# Git Commit Message Generator

このスクリプトは、作業ディレクトリで行われた変更に基づいて、Git リポジトリ用のコミットメッセージを生成します。OpenAI GPT-3.5 Turbo モデルを使用して、各論理的な変更に対して記述的で関連性のあるコミットメッセージを提供します。

# インストール
[Windows（最新版）](https://github.com/anchisan/auto-commit/releases/download/v1.0.0/auto-commit.exe)

# 手動インストール
Git コミットメッセージ生成器を使用する前に、必要な依存関係がインストールされていることを確認してください：

- Python（バージョン 3.6 以上）
- OpenAI Python ライブラリ
- Git

次のコマンドを使用して Python 依存関係を pip でインストールできます：

```shell
pip install python-dotenv openai rich
```

`.env`ファイルを作成すると環境変数を読み込むことができます:
```shell
# .env template
OPENAI_API_KEY=<YOUR_API_KEY>
TEXT_EDITOR=<YOUR_TEXT_EDITOR>
LOG_LEVEL="INFO"
```


GPT-3.5 Turbo モデルにアクセスするために、OpenAIのAPIキーを環境変数（OPENAI_API_KEY）として設定していることを確認してください。

スクリプトを使用するには、単純に次のコマンドをターミナルから実行します：

```python
python main.py
```

# オプション引数:

`--multiline (-m)`: 設定すると、コミットメッセージを複数行にすることができます。
スクリプトは対話的に、Git リポジトリの変更に基づいてコミットメッセージを選択し作成するプロセスを案内します。

# ライセンス
このプロジェクトは MIT ライセンスの下で提供されています - 詳細は LICENSE ファイルを参照してください。

# 免責事項
このリポジトリの作者とOpenAIは、このリポジトリのスクリプトによって引き起こされた結果についていかなる責任を負いません。
