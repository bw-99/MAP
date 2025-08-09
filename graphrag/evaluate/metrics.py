import numpy as np


def metrics_recall(topk_idx_lst: np.ndarray, gt_idx_lst: np.ndarray) -> float:
    return np.mean(np.any(topk_idx_lst == gt_idx_lst[:, None], axis=1))


def metrics_mrr(topk_idx_lst: np.ndarray, gt_idx_lst: np.ndarray) -> float:
    matches: np.ndarray = topk_idx_lst == gt_idx_lst[:, None]

    nonzero_row, nonzero_col = np.where(matches)
    mrr_per_sample = matches.astype(np.float32)

    mrr_per_sample[nonzero_row, nonzero_col] = 1 / (nonzero_col + 1)

    return mrr_per_sample.sum(axis=1).mean()


def metrics_ndcg(topk_idx_lst: np.ndarray, gt_idx_lst: np.ndarray) -> float:
    matches: np.ndarray = topk_idx_lst == gt_idx_lst[:, None]  # (N, K)
    found = np.any(matches, axis=1)
    ranks = np.argmax(matches, axis=1)  # 0-based

    ndcg = np.zeros_like(ranks, dtype=np.float32)
    ndcg[found] = 1.0 / np.log2(ranks[found] + 2)

    return ndcg.mean()
