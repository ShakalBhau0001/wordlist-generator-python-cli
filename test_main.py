"""Regression test: an inverted length range must fail loudly.

When --min-len exceeds --max-len no word can ever match, so the CLI must
reject the range with exit code 2 instead of writing an empty wordlist
file and reporting success.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main as wordlist_main


def test_min_len_greater_than_max_len_exits_2(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "-f", "John", "--min-len", "24", "--max-len", "7"],
    )
    with pytest.raises(SystemExit) as exc:
        wordlist_main.main()
    assert exc.value.code == 2
    assert list(tmp_path.glob("wordlist*.txt")) == []
