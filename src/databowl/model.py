"""Model training and evaluation."""

from __future__ import annotations

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split


# SAMPLE CODE!  Just to test CI
def train(X: pd.DataFrame, y: pd.Series, seed: int = 42) -> tuple[LogisticRegression, float]:
    """Train a baseline model and return it with its held-out accuracy."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed, stratify=y
    )
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    return model, model.score(X_test, y_test)
