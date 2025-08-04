import numpy as np


def metrics_recall(topk_idx_lst: np.ndarray, gt_idx_lst: np.ndarray) -> float:
    return np.mean(np.any(topk_idx_lst == gt_idx_lst[:, None], axis=1))


def metrics_mrr(topk_idx_lst: np.ndarray, gt_idx_lst: np.ndarray) -> float:
    matches = topk_idx_lst == gt_idx_lst[:, None]
    ranks = np.argmax(matches, axis=1)
    found = np.any(matches, axis=1)

    reciprocal_ranks = np.zeros_like(ranks, dtype=np.float32)
    reciprocal_ranks[found] = 1.0 / (ranks[found] + 1)

    return reciprocal_ranks.mean()


def metrics_ndcg(topk_idx_lst: np.ndarray, gt_idx_lst: np.ndarray) -> float:
    matches = topk_idx_lst == gt_idx_lst[:, None]  # (N, K)
    found = np.any(matches, axis=1)
    ranks = np.argmax(matches, axis=1)  # 0-based

    ndcg = np.zeros_like(ranks, dtype=np.float32)
    ndcg[found] = 1.0 / np.log2(ranks[found] + 2)

    return ndcg.mean()


def metrics_map(topk_idx_lst: np.ndarray, gt_idx_lst: np.ndarray) -> float:
    matches = topk_idx_lst == gt_idx_lst[:, None]  # (N, K)
    found = np.any(matches, axis=1)
    ranks = np.argmax(matches, axis=1)

    ap = np.zeros_like(ranks, dtype=np.float32)
    ap[found] = 1.0 / (ranks[found] + 1)

    return ap.mean()
