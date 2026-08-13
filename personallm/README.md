# Milli Mini LLM

石川県観光アンケート「Milli」の自由記述だけを使って、ランダム初期化から学習した小さな文字Transformerです。

## そのまま公開する

`github-pages` フォルダの中身をGitHubリポジトリの公開対象へ置けば動きます。ビルドは不要です。ローカル確認時は、ファイルを直接開かず簡易HTTPサーバーを使ってください。

```bash
python3 -m http.server 8000
```

## 再学習する（PyTorch）

```bash
pip install torch pandas onnx
python scripts/create_personas.py path/to/all.csv
python scripts/preprocess.py path/to/all.csv
python scripts/train.py --steps 2000
python scripts/export_web_model.py model/model-2000.pt
```

500 / 2,000 / 5,000 stepでチェックポイントを保存します。今回同梱したブラウザ用学習済みモデルは、同じGPT構造をTensorFlow.jsで2,000 step学習し、ブラウザ用のフラット重みへ変換したものです。

## 人物画像

20枚のWebP画像はBase64データURIへ変換し、`index.html` の `PERSONA_IMAGES` に直接埋め込んであります。公開時に人物画像ファイルを別途配置する必要はありません。

画像を差し替える場合だけ `images/persona01.webp` から `images/persona20.webp` を用意し、次を実行すると埋め込み部分を一括更新できます。

```bash
node scripts/embed_persona_images.mjs
```

## 外部AI

チャット生成時に外部LLM APIは呼びません。モデル、語彙、推論ライブラリはすべて同梱されています。

## ブラウザ推論の高速化

最大生成文字数の初期値は30文字です。生成時はTensorFlow.jsの`topk()`で候補だけを取得し、各Transformer層のKey/Valueをキャッシュして、過去のAttentionを毎文字再計算しない構造にしています。64文字のコンテキスト内に収まるよう、ペルソナIDを残しながら質問と直近の会話を調整します。
