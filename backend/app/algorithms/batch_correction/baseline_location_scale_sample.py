"""
Baseline batch effect adjustment for sample-by-feature matrices.

This is NOT ComBat (no empirical Bayes shrinkage, no design matrix for biology).
See batch_correction_method_report.json for semantics.
"""

from __future__ import annotations

import numpy as np


def per_feature_batch_location_scale_baseline(
    X: np.ndarray,
    batch_labels: np.ndarray,
    *,
    eps: float = 1e-8,
) -> np.ndarray:
    """
    For each feature j independently:
    - Compute global mean/std across all samples.
    - For each batch b, compute batch mean/std of feature j within that batch.
    - For sample i in batch b: x'[i,j] = (x[i,j] - mu_bj) / sigma_bj * sigma_j + mu_j

    Assumptions / limits:
    - Treats batch effects as per-feature additive/multiplicative shifts estimable from batch means/stds.
    - Ignores biological covariates; can attenuate or distort real biology if confounded with batch.
    - Batches with <2 samples: leaves those rows unchanged for that feature's batch stats fallback (uses global only).

    Parameters
    ----------
    X : (n_samples, n_features) float
    batch_labels : (n_samples,) object/str
    eps : floor for std to avoid division by zero
    """
    X = np.asarray(X, dtype=float)
    n, p = X.shape
    out = X.copy()
    batch_labels = np.asarray(batch_labels)

    global_mean = np.nanmean(X, axis=0)
    global_std = np.nanstd(X, axis=0, ddof=0)
    global_std = np.maximum(global_std, eps)

    unique_batches = np.unique(batch_labels)
    for b in unique_batches:
        mask = batch_labels == b
        k = int(mask.sum())
        if k == 0:
            continue
        Xb = X[mask, :]
        if k < 2:
            # Cannot estimate batch std reliably; keep original values for this batch
            continue
        bm = np.nanmean(Xb, axis=0)
        bs = np.nanstd(Xb, axis=0, ddof=0)
        bs = np.maximum(bs, eps)
        out[mask, :] = (X[mask, :] - bm) / bs * global_std + global_mean

    return out
