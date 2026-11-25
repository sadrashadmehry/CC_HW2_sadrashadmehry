"""Additional input-boundary and data-loss checks; supplied tests stay unchanged."""
from http.client import HTTPConnection

import pytest

from app import queue
from test_queue import _request, _start


@pytest.mark.parametrize("payload", ['null', '[]', '{"name":null}', '{"name":42}', '{"name":true}', '{"name":[]}'])
def test_invalid_json_shapes_leave_queue_missing(tmp_path, payload):
    port = _start(tmp_path)
    assert _request(port, "POST", "/join", payload)[0] == 400
    assert not (tmp_path / "queue.txt").exists()


@pytest.mark.parametrize("name", ["Ali\rSara", "Ali\u2028Sara", "Ali\n"])
def test_line_breaks_do_not_create_file(tmp_path, name):
    with pytest.raises(ValueError):
        queue.join(tmp_path / "queue.txt", name)
    assert not (tmp_path / "queue.txt").exists()


def test_utf8_response_content_length(tmp_path):
    port = _start(tmp_path)
    assert _request(port, "POST", "/join", '{"name":"نگار"}') == (200, "1")
    connection = HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        connection.request("POST", "/next")
        response = connection.getresponse()
        body = response.read()
        assert body == "نگار".encode("utf-8")
        assert int(response.getheader("Content-Length")) == len(body)
    finally:
        connection.close()


def test_replace_failure_preserves_queue_and_cleans_temp(tmp_path, monkeypatch):
    path = tmp_path / "queue.txt"
    path.write_text("Ali\nSara\n", encoding="utf-8")

    def fail_replace(source, target):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(queue.os, "replace", fail_replace)
    with pytest.raises(OSError):
        queue.take(path)
    assert path.read_text(encoding="utf-8") == "Ali\nSara\n"
    assert set(tmp_path.iterdir()) == {path, path.with_name(path.name + ".lock")}


