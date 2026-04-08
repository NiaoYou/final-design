"""
Autoencoder Imputer — 基于深度学习的缺失值填充

架构
----
Input(n_features) → Linear(hidden) → ReLU → BN → Dropout
                  → Linear(latent) → ReLU
                  → Linear(hidden) → ReLU → BN
                  → Linear(n_features)

训练策略（Masked Reconstruction）
----------------------------------
1. 将遮蔽位置初始化为列均值（提供合理初始输入）
2. 仅对**未被遮蔽的位置**计算重建损失（MSE），避免用遮蔽值自学习
3. 用训练好的模型对遮蔽位置做预测

参考
----
Gondara, L., & Wang, K. (2018). MIDA: Multiple imputation using denoising autoencoders.
"""

from __future__ import annotations

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


def _build_model(n_features: int, hidden_dim: int, latent_dim: int) -> "nn.Module":  # type: ignore[name-defined]
    """构建 Encoder-Decoder 模型（仅在 torch 可用时调用）。"""
    import torch.nn as nn  # noqa: F811

    class _AE(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Linear(n_features, hidden_dim),
                nn.ReLU(),
                nn.BatchNorm1d(hidden_dim),
                nn.Dropout(0.1),
                nn.Linear(hidden_dim, latent_dim),
                nn.ReLU(),
            )
            self.decoder = nn.Sequential(
                nn.Linear(latent_dim, hidden_dim),
                nn.ReLU(),
                nn.BatchNorm1d(hidden_dim),
                nn.Linear(hidden_dim, n_features),
            )

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":  # type: ignore[name-defined]
            return self.decoder(self.encoder(x))

    return _AE()


def impute_autoencoder(
    X_masked: np.ndarray,
    *,
    hidden_dim: int = 256,
    latent_dim: int = 64,
    n_epochs: int = 80,
    batch_size: int = 64,
    lr: float = 1e-3,
    random_seed: int = 42,
    device: str = "cpu",
    verbose: bool = False,
) -> np.ndarray:
    """
    用 Autoencoder 对含 NaN 的矩阵进行填充。

    Parameters
    ----------
    X_masked : np.ndarray, shape (n_samples, n_features)
        含 NaN 的输入矩阵（NaN 表示遮蔽/缺失位置）。
    hidden_dim : Encoder/Decoder 隐层维度（默认 256）。
    latent_dim : 潜空间维度（默认 64）。
    n_epochs : 训练轮数（默认 80）。
    batch_size : mini-batch 大小。
    lr : Adam 优化器学习率。
    random_seed : 随机种子。
    device : "cpu" 或 "cuda"。
    verbose : 是否每 10 epoch 打印 loss。

    Returns
    -------
    np.ndarray : 填充完成的矩阵，shape 与输入相同，不含 NaN。
    """
    if not _TORCH_AVAILABLE:
        raise ImportError("Autoencoder 填充需要 PyTorch，请运行: pip install torch")

    import torch  # noqa: F811
    import torch.optim as optim  # noqa: F811

    torch.manual_seed(random_seed)
    np.random.seed(random_seed)

    n_samples, n_features = X_masked.shape
    nan_mask = np.isnan(X_masked)  # True = 缺失位置

    # ---- 1. 初始化：缺失位置用列均值填充，作为网络初始输入 ----
    col_means = np.nanmean(X_masked, axis=0)
    col_means = np.nan_to_num(col_means, nan=0.0)
    X_init = X_masked.copy()
    for j in range(n_features):
        X_init[nan_mask[:, j], j] = col_means[j]

    X_tensor = torch.from_numpy(X_init).float().to(device)
    obs_mask = torch.from_numpy(~nan_mask).float().to(device)  # 1=已知, 0=缺失

    # ---- 2. 构建模型与优化器 ----
    model = _build_model(n_features, hidden_dim=hidden_dim, latent_dim=latent_dim).to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=n_epochs, eta_min=lr * 0.1)

    # ---- 3. 训练：仅对已知位置计算 MSE（Masked Reconstruction） ----
    model.train()
    n_batches = max(1, n_samples // batch_size)
    idx_all = np.arange(n_samples)

    for epoch in range(n_epochs):
        np.random.shuffle(idx_all)
        epoch_loss = 0.0
        for b in range(n_batches):
            batch_idx = idx_all[b * batch_size: (b + 1) * batch_size]
            if len(batch_idx) < 2:
                continue
            xb = X_tensor[batch_idx]
            mb = obs_mask[batch_idx]

            optimizer.zero_grad()
            recon = model(xb)
            # 只在观测位置计算损失，避免遮蔽值自学习
            loss = ((recon - xb) ** 2 * mb).sum() / (mb.sum() + 1e-8)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        scheduler.step()

        if verbose and (epoch + 1) % 10 == 0:
            avg = epoch_loss / n_batches
            print(f"  [AE] epoch {epoch+1}/{n_epochs}  loss={avg:.5f}")

    # ---- 4. 推断：填充缺失位置 ----
    model.eval()
    with torch.no_grad():
        X_recon = model(X_tensor).cpu().numpy()

    X_filled = X_init.copy()
    X_filled[nan_mask] = X_recon[nan_mask]

    return X_filled
