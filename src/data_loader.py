from __future__ import annotations

from pathlib import Path

import pandas as pd

from stochastic_ito_bayes_garch_strategy import load_vnindex_csv


def load_price_data(data_path: str | Path) -> pd.DataFrame:
    df = load_vnindex_csv(Path(data_path))
    df = df.sort_values("date").reset_index(drop=True)
    df["year"] = df["date"].dt.year
    return df


def chronological_split_labels(df: pd.DataFrame, train_ratio: float, valid_ratio: float) -> pd.Series:
    labels = pd.Series("test", index=df.index, dtype="object")
    train_end = int(len(df) * train_ratio)
    valid_end = int(len(df) * (train_ratio + valid_ratio))
    labels.iloc[:train_end] = "train"
    labels.iloc[train_end:valid_end] = "validation"
    labels.iloc[valid_end:] = "test"
    return labels
