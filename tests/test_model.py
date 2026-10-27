import numpy as np
import pandas as pd

from databowl.model import train


# Sample Test for CI
def test_train_returns_reasonable_accuracy():
    rng = np.random.default_rng(0)
    X = pd.DataFrame({"x": np.concatenate([rng.normal(0, 1, 100), rng.normal(5, 1, 100)])})
    y = pd.Series([0] * 100 + [1] * 100)
    model, acc = train(X, y)
    assert acc > 0.9
    assert hasattr(model, "predict")
