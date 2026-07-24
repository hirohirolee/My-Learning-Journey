import numpy as np
from sklearn.datasets import make_circles, make_moons, make_blobs


def generate_data(
    n_samples=200, noise=0.05, seed=42, dataset_type="Concentric Circles"
):
    if dataset_type in ["Concentric Circles", "同心圓"]:
        X, y = make_circles(
            n_samples=n_samples, noise=noise, factor=0.7, random_state=seed
        )
    elif dataset_type in ["Moons", "月牙形"]:
        X, y = make_moons(n_samples=n_samples, noise=noise, random_state=seed)
    elif dataset_type in ["Blobs", "群聚"]:
        X, y = make_blobs(
            n_samples=n_samples, centers=2, cluster_std=noise, random_state=seed
        )
    else:
        raise ValueError(f"Unknown dataset type: {dataset_type}")
    return X, y
