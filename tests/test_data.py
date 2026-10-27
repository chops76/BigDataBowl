import pandas as pd

from databowl.data import clean


def test_clean_drops_duplicates_and_empty_rows():
    df = pd.DataFrame({"a": [1, 1, None], "b": [2, 2, None]})
    out = clean(df)
    assert len(out) == 1
    assert list(out.columns) == ["a", "b"]
