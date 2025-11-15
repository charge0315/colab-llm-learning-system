# Google Colab でオープンソース大規模LLMをファインチューニングするノートブック / README

この README は、オープンソースの大規模 LLM（例: `gpt-oss-120B` など）を Google Colab 上でファインチューニングするためのノートブック仕様をまとめたものです。

- **ベースモデル**: Hugging Face Hub から取得  
- **学習データセット**: Hugging Face Datasets から取得  
- **学習済みモデル**: Google Drive に保存（Hugging Face 形式のディレクトリ構造）  

> ⚠️ 注意: `gpt-oss-120B` のような 100B パラメータ級モデルを「フル精度・フルファインチューニング」するのは Colab の GPU リソースでは現実的ではありません。  
> ノートブックは以下を前提に設計します。
> - 実運用は **7B〜14B クラス**のモデルを想定  
> - 100B クラスは **LoRA / QLoRA などのパラメータ効率の良い微調整**を前提とした「実験・検証用」として扱う

---

## 1. ノートブックの目的

1. Hugging Face Hub からベースモデルを取得し、Google Colab 上で読み込む  
2. Hugging Face Datasets から学習用データセットを取得し、トークナイズ・前処理を行う  
3. Parameter-Efficient Tuning（LoRA / QLoRA）を利用して LLM をファインチューニングする  
4. 学習済みモデル（もしくは LoRA アダプタ）を Google Drive に保存する  
5. 学習済みモデルを使った簡易推論（チャット / テキスト生成）をノートブック内で実行できるようにする  

---

## 2. 前提条件

### 必要なアカウント・環境

- Google アカウント  
- Google Colab（Pro / Pro+ 推奨）  
- Hugging Face アカウント  
  - `read` 権限のアクセストークン（必要に応じて `write` も）

### 必要なリソース・制限

- GPU: `T4`, `L4`, `A100` のいずれかを想定
- VRAM 16GB〜40GB を想定し、以下のような戦略をとる：
  - 7B〜14B: QLoRA もしくは 4bit / 8bit ロードでの LoRA  
  - 100B クラス: 原則として「デモ的な実験」、もしくは量子化・分割などの高度な設定が必要（このノートブックではテンプレートレベルにとどめる）

---

## 3. 依存ライブラリ

ノートブックのセットアップセルでは、以下のライブラリをインストールします。

- `transformers`
- `datasets`
- `accelerate`
- `peft`（LoRA / QLoRA 用）
- `bitsandbytes`（4bit / 8bit 量子化ロード）
- `huggingface_hub`
- `sentencepiece`（一部のトークナイザで必要）
- `trl`（必要であれば SFT 用）

インストール例（ノートブック内のセル仕様）:

```bash
!pip install -U "transformers[torch]" datasets accelerate peft bitsandbytes huggingface_hub sentencepiece trl
````

---

## 4. ノートブック構成

ノートブックは概ね次のセクションで構成します。

1. **環境準備 & Google Drive マウント**
2. **Hugging Face 認証 & ベースモデル設定**
3. **データセット取得 & 前処理**
4. **トレーニング設定（LoRA / QLoRA）**
5. **学習実行**
6. **学習済みモデルの Google Drive への保存**
7. **学習済みモデルを用いた推論デモ**
8. **オプション: Hugging Face Hub への push**

以下、各セクションの仕様を詳細に記述します。

---

## 5. 各セクション詳細仕様

### 5.1 環境準備 & Google Drive マウント

#### 目的

* Colab ランタイム情報の確認（GPU 種類など）
* Google Drive を `/content/drive` にマウント
* モデル保存用ディレクトリを作成

#### 主な処理内容

* GPU 情報の表示（`!nvidia-smi`）
* Google Drive マウント：

```python
from google.colab import drive
drive.mount('/content/drive')
```

* 保存先ルートディレクトリ（例）：

```python
BASE_SAVE_DIR = "/content/drive/MyDrive/llm-finetune"
PROJECT_NAME = "gpt-oss-120b-lora-demo"  # ユーザーが変更
OUTPUT_DIR = f"{BASE_SAVE_DIR}/{PROJECT_NAME}"
```

---

### 5.2 Hugging Face 認証 & ベースモデル設定

#### 目的

* Hugging Face のアクセストークンを入力／環境変数に設定
* ベースモデルとトークナイザの ID を指定

#### 主なパラメータ

```python
HF_TOKEN = "xxxxxxxxxxxxxxxx"  # ノートブックでは input() を使って安全に入力させる
BASE_MODEL_ID = "Qwen/Qwen2-7B"      # 例: 実運用向け
# BASE_MODEL_ID = "gpt-oss/gpt-oss-120B"  # 例: 超大規模モデル（あくまでテンプレ）
USE_4BIT = True                      # QLoRA 用
```

#### 認証

```python
from huggingface_hub import login
login(token=HF_TOKEN)
```

---

### 5.3 データセット取得 & 前処理

#### 目的

* Hugging Face Datasets から学習データセットを取得
* テキストカラムを指定してトークナイズ・パッキング

#### 主なパラメータ

```python
DATASET_ID = "iac/ja-wiki-2023"  # 例: ユーザーが任意の日本語／英語データセットに変更可能
DATASET_SPLIT = "train"
TEXT_COLUMN = "text"

MAX_SEQ_LENGTH = 1024
PACKING = True  # 文書を詰めて固定長のシーケンスにするか
```

#### 主な処理

* `datasets.load_dataset` でデータセット取得
* `transformers.AutoTokenizer` でトークナイザ読み込み

  * `padding=False`, `truncation=True`, `return_special_tokens_mask=True` などを設定
* `map` を使ってトークナイズ
* PACKING を有効にする場合は、複数サンプルを連結して固定長にカットする関数を用意

---

### 5.4 トレーニング設定（LoRA / QLoRA）

#### 目的

* VRAM 制約下でも学習可能なように LoRA / QLoRA を前提とした設定を行う
* `peft` を利用してベースモデルに LoRA アダプタを注入

#### 主なパラメータ

```python
LORA_R = 64
LORA_ALPHA = 16
LORA_DROPOUT = 0.05
LORA_TARGET_MODULES = ["q_proj", "v_proj"]  # モデルに応じて調整

BATCH_SIZE = 1
GRADIENT_ACCUMULATION_STEPS = 16
LEARNING_RATE = 2e-4
NUM_TRAIN_EPOCHS = 2
WARMUP_STEPS = 100
LOGGING_STEPS = 10
SAVE_STEPS = 500
MAX_STEPS = -1  # 任意でステップ数を制限
```

#### モデルロード仕様

* `transformers.AutoModelForCausalLM.from_pretrained` を使用
* 4bit / 8bit ロード（QLoRA）の場合：

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype="bfloat16",
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_ID,
    quantization_config=bnb_config,
    device_map="auto"
)
```

* `peft.get_peft_model` により LoRA アダプタを注入

---

### 5.5 学習実行

#### 目的

* `transformers.Trainer` または `trl.SFTTrainer` を使用してトレーニングを実行
* ロス・学習進捗をログ出力

#### 学習ループ仕様

* `TrainingArguments` に以下を設定：

  * `output_dir=OUTPUT_DIR + "/checkpoints"`
  * `per_device_train_batch_size=BATCH_SIZE`
  * `gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS`
  * `learning_rate=LEARNING_RATE`
  * `num_train_epochs=NUM_TRAIN_EPOCHS`
  * `logging_steps=LOGGING_STEPS`
  * `save_steps=SAVE_STEPS`
  * `bf16=True` (GPU が対応している場合)
  * `evaluation_strategy="no"`（必要に応じて `steps` などに変更）

* Colab のセッション切断対策として：

  * チェックポイントをこまめに保存
  * 必要であれば `max_steps` で区切って何度かに分けて学習

---

### 5.6 学習済みモデルの Google Drive への保存

#### 目的

* 学習済みモデル（LoRA アダプタを含む）を Google Drive 上に永続化
* Hugging Face 互換のディレクトリとして保存

#### 保存仕様

* ディレクトリ構造（例）：

```text
/content/drive/MyDrive/llm-finetune/
  └── gpt-oss-120b-lora-demo/
      ├── checkpoints/
      │   └── checkpoint-xxxx/
      └── final/
          ├── adapter_model.bin
          ├── adapter_config.json
          ├── tokenizer.json
          ├── tokenizer_config.json
          ├── config.json
          └── README.md（任意）
```

* 保存処理例（ノートブック側仕様）：

```python
FINAL_DIR = f"{OUTPUT_DIR}/final"

# LoRA アダプタを保存
model.save_pretrained(FINAL_DIR)
tokenizer.save_pretrained(FINAL_DIR)
```

> フルモデルをマージして保存したい場合は、`peft` の merge 機能を使うが、VRAM / RAM 使用量が増えるためオプション扱いとする。

---

### 5.7 学習済みモデルを用いた推論デモ

#### 目的

* 学習済みモデル（LoRA アダプタ含む）を読み込み、簡単なプロンプトに対して推論を行う
* チャット形式／テキスト補完形式のどちらでもよい

#### 主な仕様

* 学習セクションとは独立したセルで、再度モデルをロード:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_ID,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(FINAL_DIR)
model = PeftModel.from_pretrained(base_model, FINAL_DIR)
model.eval()
```

* シンプルな推論関数を用意：

```python
def generate_text(prompt, max_new_tokens=128):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            top_p=0.95,
            temperature=0.7
        )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)
```

* テスト用プロンプト例や、対話的に入力できるセルを用意

---

### 5.8 オプション: Hugging Face Hub への push

#### 目的

* 希望する場合、Google Drive からローカルにコピーして Hugging Face Hub に `push_to_hub` する

#### 主な仕様

* `model.push_to_hub("username/project-name")`
* `tokenizer.push_to_hub("username/project-name")`

Colab 上で直接実行できるが、トークンの権限とプライバシーに注意する旨を記載。

---

## 6. 設定パラメータ一覧（テンプレ）

ノートブック冒頭近くに「まとめて編集できる設定セル」を用意する。

```python
# プロジェクト設定
PROJECT_NAME = "gpt-oss-120b-lora-demo"
BASE_SAVE_DIR = "/content/drive/MyDrive/llm-finetune"

# モデル設定
BASE_MODEL_ID = "Qwen/Qwen2-7B"
USE_4BIT = True

# データセット設定
DATASET_ID = "iac/ja-wiki-2023"
DATASET_SPLIT = "train"
TEXT_COLUMN = "text"
MAX_SEQ_LENGTH = 1024
PACKING = True

# LoRA / トレーニング設定
LORA_R = 64
LORA_ALPHA = 16
LORA_DROPOUT = 0.05
LORA_TARGET_MODULES = ["q_proj", "v_proj"]

BATCH_SIZE = 1
GRADIENT_ACCUMULATION_STEPS = 16
LEARNING_RATE = 2e-4
NUM_TRAIN_EPOCHS = 2
WARMUP_STEPS = 100
LOGGING_STEPS = 10
SAVE_STEPS = 500
MAX_STEPS = -1  # 制限しない場合は -1
```

---

## 7. 制限事項・注意点

* Colab のセッションは数時間で切断されるため、**こまめなチェックポイント保存**が必須
* 100B パラメータ級モデルについて：

  * フルチューニングはほぼ不可能
  * QLoRA + 一部層のみ学習 + 積極的な量子化・オフロードが前提
* 公開データセットを利用する際は、必ずライセンスを確認すること
* 学習済みモデルを公開する場合も、ベースモデルおよびデータセットのライセンス条件に従うこと

---

## 8. 今後の拡張案

* WandB / TensorBoard と連携した学習ログ可視化
* 評価用データセット（validation split）を使った定期評価
* RAG（Retrieval-Augmented Generation）との組み合わせ
* vLLM などの高速推論エンジンと連携したデプロイノートブック

---

この README をもとに、Google Colab ノートブックでは「上から順にセルを実行していけば、
Hugging Face からモデル・データセットを取得 → Colab でファインチューニング → 学習済みモデルを Google Drive に保存 → 推論デモ」
まで一通り完結するように実装してください。

```
```
