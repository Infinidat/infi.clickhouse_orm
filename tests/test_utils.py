# -*- coding: utf-8 -*-
from clickhouse_orm.utils import escape, unescape

SPECIAL_CHARS = {"\b": "\\x08", "\f": "\\x0c", "\r": "\\r", "\n": "\\n", "\t": "\\t", "\0": "\\x00", "\\": "\\\\", "'": "\\'"}


def test_unescape():

    for input_, expected in (
        ("π\\t", "π\t"),
        ("\\new", "\new"),
        ("cheeky 🐵", "cheeky 🐵"),
        ("\\N", None),
    ):
        assert unescape(input_) == expected


def test_escape_special_chars():

    initial = "".join(SPECIAL_CHARS.keys())
    expected = "".join(SPECIAL_CHARS.values())
    assert escape(initial, quote=False) == expected
    assert escape(initial) == "'" + expected + "'"


def test_escape_unescape_parity():

    for initial in ("π\t", "\new", "cheeky 🐵", "back \\ slash", "\\\\n"):
        assert unescape(escape(initial, quote=False)) == initial
