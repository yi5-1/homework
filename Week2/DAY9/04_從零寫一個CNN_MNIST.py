# 04 — 從零寫一個 CNN，訓練 MNIST 手寫數字辨識
#
# 目的：打開 CNN 這個黑箱，看它到底長怎樣、怎麼訓練
# 用最少的程式碼達到 >98% 準確率
#
# 需要：pip install tensorflow matplotlib numpy

import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import layers, models

plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei"]
plt.rcParams["axes.unicode_minus"] = False

# ====== 1) 載入資料 ======
# MNIST 是 keras 內建：60000 張訓練 + 10000 張測試，每張 28x28 灰階
(x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
print(f"訓練資料：{x_train.shape}，測試資料：{x_test.shape}")

# 正規化 [0, 255] → [0, 1]，加上 channel 維度 (28,28) → (28,28,1)
x_train = (x_train.astype("float32") / 255.0)[..., None]
x_test  = (x_test.astype("float32")  / 255.0)[..., None]

# ====== 2) 蓋一個小 CNN ======
# 結構：Conv → Pool → Conv → Pool → Flatten → Dense → Softmax
model = models.Sequential([
    layers.Input(shape=(28, 28, 1)),

    # 第 1 層卷積：16 個 3x3 filter，找低階特徵（線條、邊）
    layers.Conv2D(16, kernel_size=3, activation="relu"),
    layers.MaxPool2D(pool_size=2),                       # 28→13

    # 第 2 層卷積：32 個 3x3 filter，找中階特徵（角、彎曲）
    layers.Conv2D(32, kernel_size=3, activation="relu"),
    layers.MaxPool2D(pool_size=2),                       # 13→5

    # 攤平 → 全連接 → 10 類機率
    layers.Flatten(),
    layers.Dense(64, activation="relu"),
    layers.Dense(10, activation="softmax"),
])

model.summary()   # 看每層 output shape 跟參數量

# ====== 3) 編譯 + 訓練 ======
model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",     # 標籤是整數 0~9
    metrics=["accuracy"],
)

# 5 epochs 通常就 >98%；CPU 上約 1~3 分鐘
history = model.fit(
    x_train, y_train,
    epochs=5, batch_size=128,
    validation_split=0.1,
    verbose=1,
)

# ====== 4) 測試集評估 ======
test_loss, test_acc = model.evaluate(x_test, y_test, verbose=0)
print(f"\n測試集準確率：{test_acc * 100:.2f}%")

# ====== 5) 畫學習曲線 ======
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].plot(history.history["accuracy"],     label="train")
axes[0].plot(history.history["val_accuracy"], label="val")
axes[0].set_title("準確率"); axes[0].set_xlabel("epoch"); axes[0].legend()
axes[1].plot(history.history["loss"],     label="train")
axes[1].plot(history.history["val_loss"], label="val")
axes[1].set_title("損失 (loss)"); axes[1].set_xlabel("epoch"); axes[1].legend()
plt.tight_layout(); plt.show()

# ====== 6) 秀 10 張測試圖 + 預測 ======
sample = x_test[:10]
preds  = model.predict(sample, verbose=0).argmax(axis=1)

plt.figure(figsize=(15, 2.5))
for i in range(10):
    plt.subplot(1, 10, i + 1)
    plt.imshow(sample[i].squeeze(), cmap="gray")
    color = "green" if preds[i] == y_test[i] else "red"
    plt.title(f"預測:{preds[i]}\n真實:{y_test[i]}", color=color, fontsize=10)
    plt.axis("off")
plt.tight_layout(); plt.show()

# ====== 7) 存下訓練好的模型（可選）======
# model.save("mnist_cnn.h5")
# print("模型已存到 mnist_cnn.h5")
