import subprocess
import zipfile

import pytest

from databowl import download as dl


def _fake_run_factory(dest, competition):
    def fake_run(cmd, check):
        with zipfile.ZipFile(dest / f"{competition}.zip", "w") as zf:
            zf.writestr("players.csv", "id,name\n1,A\n")
        return subprocess.CompletedProcess(cmd, 0)

    return fake_run


def test_download_unzips_and_removes_archive(tmp_path, monkeypatch):
    monkeypatch.setattr(dl.shutil, "which", lambda _: "/usr/bin/kaggle")
    monkeypatch.setattr(dl.subprocess, "run", _fake_run_factory(tmp_path, "comp"))
    dl.download("comp", tmp_path)
    assert (tmp_path / "players.csv").exists()
    assert not (tmp_path / "comp.zip").exists()


def test_download_skips_when_data_present(tmp_path, monkeypatch):
    (tmp_path / "existing.csv").write_text("x")

    def boom(*a, **k):
        raise AssertionError("should not download")

    monkeypatch.setattr(dl.subprocess, "run", boom)
    dl.download("comp", tmp_path)  # no error -> skipped


def test_missing_cli_gives_helpful_exit(tmp_path, monkeypatch):
    monkeypatch.setattr(dl.shutil, "which", lambda _: None)
    with pytest.raises(SystemExit, match="kaggle CLI not found"):
        dl.download("comp", tmp_path)
