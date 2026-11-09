# 02 — Teachable Machine 手把手

Google 做的**不寫程式碼**訓練分類器工具。5 分鐘就能生出一個 CNN 模型。

網址：<https://teachablemachine.withgoogle.com/>

---

## 底下藏了什麼

TM 用一個叫 **MobileNet** 的預訓練 CNN 當骨幹（在 ImageNet 上訓練過的），只重新訓練最後幾層來認你給的類別。這種做法叫 **遷移學習** (transfer learning) —— 就算你只給 30 張圖也能訓練得動。

輸入尺寸：**224 × 224 × 3**（RGB）。任何進來的圖片都要縮到這個大小。

---

## Step-by-step

### 1) 進網站 → 選 Image Project → Standard image model

![選 Image Project](//placeholder — 網站自己有畫面)

### 2) 建立至少 2 個類別

點左邊 `Class 1`、`Class 2` 的鉛筆改名字，例如：
- `Class 1` → `剪刀`
- `Class 2` → `石頭`
- 新增 `Class 3` → `布`

**點 Add a class 可以加更多**。至少 2 類才能訓練。

### 3) 收集樣本

每個類別下面有 **Webcam** 和 **Upload** 兩個按鈕。

**建議用 Webcam**：
- 點 `Webcam` → 授權瀏覽器用鏡頭
- **按住** `Hold to Record` 錄一段（自動抓每一 frame 當一張樣本）
- 每類**至少 30 張**，最好 100+
- 錄的時候**動一動**：轉角度、換位置、改光線 → 樣本越多樣，模型越 robust

**收樣本的小技巧**：
- 背景保持一致，避免模型學到「背景」而不是「物體」
- 或反過來：故意換各種背景，強迫模型忽略背景
- 每一類的樣本數量**盡量差不多**，不然模型會偏向某一類

### 4) 訓練

右邊點 `Train Model`。**訓練期間不要關瀏覽器分頁**（在你電腦上跑，非雲端）。

- 進階設定：`Epochs` 預設 50，資料少可以調小；`Batch Size` / `Learning Rate` 一般不動
- CPU 也跑得動，通常 30 秒 ~ 2 分鐘

### 5) 測試

右邊的 Preview 會自動用你的 webcam 即時預測。手勢做給它看，看有沒有分對。

**沒分對怎麼辦？** 通常是樣本問題：
- 樣本太少 → 每類再多錄一些
- 樣本太單一 → 換角度 / 光線再錄
- 兩類長太像 → 你自己看都分不出來的模型也分不出來

### 6) 匯出模型

點右上 `Export Model` → 選 `Tensorflow` → 選 `Keras` → 點 `Download my model`。

會下載一個 `.zip`，解壓縮後裡面有：

| 檔案 | 用途 |
|---|---|
| `keras_model.h5` | 訓練好的模型權重 |
| `labels.txt` | 類別名字對照表（`0 剪刀`、`1 石頭`、...）|

把這兩個檔案放到 `03_載入TM模型_鏡頭辨識.py` 同一個資料夾。

---

## TM 用了什麼正規化

匯出的模型期待輸入：
- 大小 `224 x 224`
- 通道順序 **RGB**（OpenCV 預設是 BGR，要 `cv2.cvtColor(..., cv2.COLOR_BGR2RGB)`）
- 像素值範圍 `[-1, 1]`（`img / 127.5 - 1`）

`03_載入TM模型_鏡頭辨識.py` 已經幫你做好這些預處理。

---

## 你可能會踩的坑

1. **TF 版本相容**：TM 匯出的 `.h5` 是舊格式，Keras 3 有時讀不動。要用 TF 2.15 附的 keras（`tf.keras.models.load_model` 而不是純 `keras.models.load_model`）。
2. **模型檔太大**：MobileNet backbone 有點大（10+ MB），別上傳到 GitHub（放 `.gitignore` 裡）。
3. **訓練當下瀏覽器要開著**：TM 是本地端算的，關掉分頁就中斷。
4. **鏡頭權限**：Chrome 要允許存取 webcam 才錄得到樣本。

---

## 下一步

去跑 `03_載入TM模型_鏡頭辨識.py` — 把你剛才訓練好的模型接上鏡頭，看它即時分類。
