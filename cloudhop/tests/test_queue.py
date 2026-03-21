"""Comprehensive tests for CloudHop transfer queue system."""

import json
import threading
from unittest.mock import MagicMock, patch

import pytest

from cloudhop.transfer import TransferManager


@pytest.fixture
def manager(tmp_path):
    """Create a TransferManager with a temporary directory."""
    return TransferManager(cm_dir=str(tmp_path))


# ---------------------------------------------------------------------------
# 1. test_queue_add_and_list: add 3 items, verify order
# ---------------------------------------------------------------------------


class TestQueueAddAndList:
    def test_add_three_items_and_verify_order(self, manager):
        """Add 3 items and verify they appear in insertion order."""
        r1 = manager.queue_add({"source": "gdrive:", "dest": "onedrive:"})
        r2 = manager.queue_add({"source": "dropbox:", "dest": "s3:backup"})
        r3 = manager.queue_add({"source": "mega:", "dest": "b2:archive"})

        assert r1["ok"] is True
        assert r2["ok"] is True
        assert r3["ok"] is True
        assert "queue_id" in r1
        assert "queue_id" in r2
        assert "queue_id" in r3

        items = manager.queue_list()
        assert len(items) == 3
        assert items[0]["config"]["source"] == "gdrive:"
        assert items[1]["config"]["source"] == "dropbox:"
        assert items[2]["config"]["source"] == "mega:"
        # All should be waiting
        assert all(i["status"] == "waiting" for i in items)
        # All should have added_at timestamps
        assert all("added_at" in i for i in items)
        # All queue_ids should be unique
        ids = [i["queue_id"] for i in items]
        assert len(set(ids)) == 3


# ---------------------------------------------------------------------------
# 2. test_queue_remove: add, remove, verify it's gone
# ---------------------------------------------------------------------------


class TestQueueRemove:
    def test_remove_by_queue_id(self, manager):
        """Add an item, remove it, verify it's gone."""
        r = manager.queue_add({"source": "a:", "dest": "b:"})
        queue_id = r["queue_id"]
        assert len(manager.queue_list()) == 1

        result = manager.queue_remove(queue_id)
        assert result is True
        assert len(manager.queue_list()) == 0

    def test_remove_nonexistent_returns_false(self, manager):
        """Removing a nonexistent queue_id returns False."""
        assert manager.queue_remove("nonexistent") is False

    def test_cannot_remove_active_item(self, manager):
        """Cannot remove an item with status 'active'."""
        manager.queue = [
            {
                "queue_id": "active_item",
                "status": "active",
                "config": {"source": "a:", "dest": "b:"},
            }
        ]
        assert manager.queue_remove("active_item") is False
        assert len(manager.queue) == 1


# ---------------------------------------------------------------------------
# 3. test_queue_process_next: mock transfer completion, verify next starts
# ---------------------------------------------------------------------------


class TestQueueProcessNext:
    @patch("subprocess.Popen")
    @patch("os.path.exists", return_value=True)
    def test_process_next_starts_waiting(self, mock_exists, mock_popen, manager):
        """queue_process_next starts the next waiting transfer."""
        mock_proc = MagicMock()
        mock_proc.pid = 9999
        mock_popen.return_value = mock_proc

        manager.queue = [
            {
                "queue_id": "finished1",
                "status": "active",
                "config": {
                    "source": "/tmp/a",
                    "dest": "/tmp/b",
                    "source_type": "local",
                    "dest_type": "local",
                },
            },
            {
                "queue_id": "next1",
                "status": "waiting",
                "added_at": "2025-01-01T00:00:00",
                "config": {
                    "source": "/tmp/c",
                    "dest": "/tmp/d",
                    "source_type": "local",
                    "dest_type": "local",
                },
            },
        ]
        result = manager.queue_process_next()
        assert result["ok"] is True
        # First item should be completed, second should be active
        assert manager.queue[0]["status"] == "completed"
        assert manager.queue[1]["status"] == "active"

    def test_process_next_empty_queue(self, manager):
        """Returns error when queue is empty."""
        result = manager.queue_process_next()
        assert result["ok"] is False
        assert "empty" in result["msg"].lower()

    def test_process_next_all_completed(self, manager):
        """Returns error when all items are completed (no waiting items)."""
        manager.queue = [
            {"queue_id": "done1", "status": "completed", "config": {"source": "a:", "dest": "b:"}},
        ]
        result = manager.queue_process_next()
        assert result["ok"] is False


# ---------------------------------------------------------------------------
# 4. test_queue_persistence: save, reload, verify data persists
# ---------------------------------------------------------------------------


class TestQueuePersistence:
    def test_save_and_reload(self, manager):
        """Queue persists to disk and survives reload."""
        manager.queue_add({"source": "gdrive:", "dest": "onedrive:"})
        manager.queue_add({"source": "dropbox:", "dest": "s3:"})
        assert len(manager.queue) == 2

        # Force reload from disk
        manager._load_queue()
        assert len(manager.queue) == 2
        assert manager.queue[0]["config"]["source"] == "gdrive:"
        assert manager.queue[1]["config"]["source"] == "dropbox:"
        # Status preserved
        assert manager.queue[0]["status"] == "waiting"

    def test_corrupt_json_resets_to_empty(self, manager):
        """Corrupt queue.json resets to empty list."""
        with open(manager.queue_file, "w") as f:
            f.write("{not valid json")
        manager._load_queue()
        assert manager.queue == []

    def test_non_list_json_resets_to_empty(self, manager):
        """queue.json with non-list content resets to empty."""
        with open(manager.queue_file, "w") as f:
            json.dump({"not": "a list"}, f)
        manager._load_queue()
        assert manager.queue == []

    def test_missing_file_gives_empty_queue(self, tmp_path):
        """Missing queue.json gives empty queue."""
        m = TransferManager(cm_dir=str(tmp_path))
        assert m.queue == []


# ---------------------------------------------------------------------------
# 5. test_queue_reorder: move item from position 3 to position 1
# ---------------------------------------------------------------------------


class TestQueueReorder:
    def test_reorder_move_last_to_first(self, manager):
        """Move item from position 2 (third) to position 0 (first)."""
        r1 = manager.queue_add({"source": "a:", "dest": "b:"})
        r2 = manager.queue_add({"source": "c:", "dest": "d:"})
        r3 = manager.queue_add({"source": "e:", "dest": "f:"})

        assert manager.queue_reorder(r3["queue_id"], 0) is True
        items = manager.queue_list()
        assert items[0]["queue_id"] == r3["queue_id"]
        assert items[1]["queue_id"] == r1["queue_id"]
        assert items[2]["queue_id"] == r2["queue_id"]

    def test_reorder_move_first_to_last(self, manager):
        """Move item from position 0 to position 2."""
        r1 = manager.queue_add({"source": "a:", "dest": "b:"})
        r2 = manager.queue_add({"source": "c:", "dest": "d:"})
        r3 = manager.queue_add({"source": "e:", "dest": "f:"})

        assert manager.queue_reorder(r1["queue_id"], 2) is True
        items = manager.queue_list()
        assert items[0]["queue_id"] == r2["queue_id"]
        assert items[1]["queue_id"] == r3["queue_id"]
        assert items[2]["queue_id"] == r1["queue_id"]

    def test_reorder_same_position(self, manager):
        """Moving to same position returns True (no-op)."""
        r1 = manager.queue_add({"source": "a:", "dest": "b:"})
        assert manager.queue_reorder(r1["queue_id"], 0) is True

    def test_reorder_invalid_id_returns_false(self, manager):
        """Invalid queue_id returns False."""
        assert manager.queue_reorder("nonexistent", 0) is False

    def test_reorder_invalid_position_returns_false(self, manager):
        """Out-of-range position returns False."""
        r1 = manager.queue_add({"source": "a:", "dest": "b:"})
        assert manager.queue_reorder(r1["queue_id"], 99) is False
        assert manager.queue_reorder(r1["queue_id"], -1) is False

    def test_reorder_persists_to_disk(self, manager):
        """Reorder is saved to disk."""
        manager.queue_add({"source": "a:", "dest": "b:"})
        r2 = manager.queue_add({"source": "c:", "dest": "d:"})
        manager.queue_reorder(r2["queue_id"], 0)
        # Reload and verify
        manager._load_queue()
        assert manager.queue[0]["queue_id"] == r2["queue_id"]


# ---------------------------------------------------------------------------
# 6. test_queue_api_endpoints: tests for all 4 endpoints
# ---------------------------------------------------------------------------


class TestQueueAPIEndpoints:
    """Integration tests for queue API endpoints.

    Uses the same server_fixture pattern from test_server_integration.py.
    """

    @pytest.fixture
    def server_fixture(self, tmp_path):
        import http.server

        from cloudhop.server import CSRF_TOKEN, CloudHopHandler

        mgr = TransferManager(cm_dir=str(tmp_path))
        mgr.log_file = str(tmp_path / "test.log")
        with open(mgr.log_file, "w") as f:
            f.write("2025/06/10 10:00:00 INFO  :\n")
            f.write("Transferred:   \t  100 MiB / 1.000 GiB, 10%, 50.000 MiB/s, ETA 30s\n")
            f.write("Transferred:            5 / 50, 10%\n")
            f.write("Errors:                 0\n")
            f.write("Elapsed time:      30.0s\n")
        CloudHopHandler.manager = mgr
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), CloudHopHandler)
        port = server.server_address[1]
        CloudHopHandler.actual_port = port
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        yield {"port": port, "manager": mgr, "csrf": CSRF_TOKEN}
        server.shutdown()

    def _req(self, port, method, path, body=None, csrf=None):
        import urllib.request

        from cloudhop.server import CSRF_TOKEN

        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}{path}",
            data=data,
            method=method,
        )
        req.add_header("Host", f"localhost:{port}")
        req.add_header("Content-Type", "application/json")
        req.add_header("X-CSRF-Token", csrf or CSRF_TOKEN)
        return req

    def _fetch(self, req):
        import urllib.request

        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())

    def test_post_queue_add(self, server_fixture):
        """POST /api/queue/add returns queue_id."""
        port = server_fixture["port"]
        data = self._fetch(
            self._req(port, "POST", "/api/queue/add", {"source": "gdrive:", "dest": "s3:"})
        )
        assert data["ok"] is True
        assert "queue_id" in data

    def test_get_queue_list(self, server_fixture):
        """GET /api/queue returns all items."""
        port = server_fixture["port"]
        self._fetch(self._req(port, "POST", "/api/queue/add", {"source": "a:", "dest": "b:"}))
        data = self._fetch(self._req(port, "GET", "/api/queue"))
        assert "queue" in data
        assert len(data["queue"]) == 1
        assert data["queue"][0]["config"]["source"] == "a:"

    def test_delete_queue_item(self, server_fixture):
        """DELETE /api/queue/<queue_id> removes item."""
        port = server_fixture["port"]
        add_data = self._fetch(
            self._req(port, "POST", "/api/queue/add", {"source": "a:", "dest": "b:"})
        )
        qid = add_data["queue_id"]
        del_data = self._fetch(self._req(port, "DELETE", f"/api/queue/{qid}"))
        assert del_data["ok"] is True
        # Verify removed
        list_data = self._fetch(self._req(port, "GET", "/api/queue"))
        assert len(list_data["queue"]) == 0

    def test_put_queue_reorder(self, server_fixture):
        """PUT /api/queue/<queue_id>/reorder moves item."""
        port = server_fixture["port"]
        r1 = self._fetch(self._req(port, "POST", "/api/queue/add", {"source": "a:", "dest": "b:"}))
        r2 = self._fetch(self._req(port, "POST", "/api/queue/add", {"source": "c:", "dest": "d:"}))
        # Move second to first
        reorder_data = self._fetch(
            self._req(port, "PUT", f"/api/queue/{r2['queue_id']}/reorder", {"position": 0})
        )
        assert reorder_data["ok"] is True
        # Verify order
        list_data = self._fetch(self._req(port, "GET", "/api/queue"))
        assert list_data["queue"][0]["queue_id"] == r2["queue_id"]
        assert list_data["queue"][1]["queue_id"] == r1["queue_id"]


# ---------------------------------------------------------------------------
# 7. test_queue_thread_safety: concurrent operations on queue
# ---------------------------------------------------------------------------


class TestQueueThreadSafety:
    def test_concurrent_adds(self, manager):
        """Multiple threads adding to the queue simultaneously."""
        errors = []
        barrier = threading.Barrier(10)

        def adder(idx):
            try:
                barrier.wait(timeout=5)
                result = manager.queue_add({"source": f"src{idx}:", "dest": f"dst{idx}:"})
                assert result["ok"] is True
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=adder, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Thread errors: {errors}"
        assert len(manager.queue_list()) == 10

    def test_concurrent_add_and_remove(self, manager):
        """Concurrent adds and removes don't corrupt the queue."""
        # Pre-populate
        ids = []
        for i in range(5):
            r = manager.queue_add({"source": f"s{i}:", "dest": f"d{i}:"})
            ids.append(r["queue_id"])

        errors = []
        barrier = threading.Barrier(10)

        def adder(idx):
            try:
                barrier.wait(timeout=5)
                manager.queue_add({"source": f"new{idx}:", "dest": f"new_d{idx}:"})
            except Exception as e:
                errors.append(str(e))

        def remover(qid):
            try:
                barrier.wait(timeout=5)
                manager.queue_remove(qid)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=adder, args=(i,)) for i in range(5)]
        threads += [threading.Thread(target=remover, args=(qid,)) for qid in ids]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Thread errors: {errors}"
        # Queue should be valid JSON on disk
        with open(manager.queue_file) as f:
            data = json.load(f)
        assert isinstance(data, list)

    def test_concurrent_reorder(self, manager):
        """Concurrent reorder operations don't crash."""
        for i in range(5):
            manager.queue_add({"source": f"s{i}:", "dest": f"d{i}:"})
        items = manager.queue_list()
        errors = []
        barrier = threading.Barrier(5)

        def reorderer(idx):
            try:
                barrier.wait(timeout=5)
                qid = items[idx % len(items)]["queue_id"]
                manager.queue_reorder(qid, (idx + 2) % len(items))
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=reorderer, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Thread errors: {errors}"
        # Queue should still be valid
        assert len(manager.queue_list()) == 5


# ---------------------------------------------------------------------------
# 8. test_queue_auto_start_on_completion: end-to-end
# ---------------------------------------------------------------------------


class TestQueueAutoStartOnCompletion:
    @patch("subprocess.Popen")
    @patch("os.path.exists", return_value=True)
    def test_auto_start_next_when_transfer_finishes(self, mock_exists, mock_popen, manager):
        """When a transfer finishes, the background scanner auto-starts the next."""
        mock_proc = MagicMock()
        mock_proc.pid = 7777
        mock_proc.poll.return_value = None  # process is running
        mock_popen.return_value = mock_proc

        # Add two transfers to queue
        manager.queue_add(
            {"source": "/tmp/a", "dest": "/tmp/b", "source_type": "local", "dest_type": "local"}
        )
        manager.queue_add(
            {"source": "/tmp/c", "dest": "/tmp/d", "source_type": "local", "dest_type": "local"}
        )

        # Start first transfer via queue
        result = manager.queue_process_next()
        assert result["ok"] is True
        assert manager.queue[0]["status"] == "active"
        assert manager.queue[1]["status"] == "waiting"

        # Simulate transfer completion: process exits
        mock_proc.poll.return_value = 0  # process finished
        manager._rclone_proc = mock_proc
        manager.rclone_pid = 7777
        manager.transfer_active = True
        # is_rclone_running should now return False
        assert manager.is_rclone_running() is False

        # Create a new mock for the next transfer start
        mock_proc2 = MagicMock()
        mock_proc2.pid = 8888
        mock_popen.return_value = mock_proc2

        # Process next (what background_scanner would do)
        result2 = manager.queue_process_next()
        assert result2["ok"] is True
        assert manager.queue[0]["status"] == "completed"
        assert manager.queue[1]["status"] == "active"

    def test_no_crash_when_queue_empty_after_completion(self, manager):
        """queue_process_next does nothing when queue is empty after a completion."""
        manager.queue = [
            {
                "queue_id": "done1",
                "status": "active",
                "config": {"source": "a:", "dest": "b:"},
            },
        ]
        result = manager.queue_process_next()
        # First item marked completed, but no next waiting
        assert result["ok"] is False
        assert manager.queue[0]["status"] == "completed"
