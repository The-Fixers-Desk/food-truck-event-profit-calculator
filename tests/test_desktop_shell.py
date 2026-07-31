from pathlib import Path
from urllib.error import URLError

import pytest

from app import create_app
from app.desktop import (
    ALREADY_OPEN_HTML,
    LOADING_HTML,
    LOOPBACK_HOST,
    PRODUCT_NAME,
    STARTUP_ERROR_HTML,
    DesktopLifecycle,
    InstanceAlreadyRunning,
    LocalServer,
    SingleInstanceLock,
    allowed_primary_navigation,
    desktop_data_paths,
    run_desktop,
)


class Event:
    def __init__(self):
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self


class FakeWindow:
    def __init__(self):
        self.events = type("Events", (), {"closed": Event()})()
        self.loaded_urls = []
        self.loaded_html = []

    def load_url(self, url):
        self.loaded_urls.append(url)

    def load_html(self, html):
        self.loaded_html.append(html)


class FakeWebview:
    def __init__(self):
        self.created = []
        self.window = FakeWindow()
        self.start_callbacks = []

    def create_window(self, title, **kwargs):
        self.created.append((title, kwargs))
        return self.window

    def start(self, callback=None):
        self.start_callbacks.append(callback)
        if callback:
            callback()


class FakeServer:
    instances = []

    def __init__(self, application):
        self.application = application
        self.url = "http://127.0.0.1:54321/"
        self.calls = []
        self.thread_alive = False
        FakeServer.instances.append(self)

    def start(self):
        self.calls.append("start")

    def wait_until_ready(self):
        self.calls.append("ready")

    def shutdown(self):
        self.calls.append("shutdown")


def isolated_app(root: Path):
    return create_app(
        {
            "DATA_ROOT": root,
            "DATABASE": root / "app.db",
            "ENFORCE_SETUP": False,
            "TESTING": True,
        }
    )


def test_local_server_binds_loopback_available_port_and_shuts_down(tmp_path):
    server = LocalServer(isolated_app(tmp_path))

    assert server.url.startswith(f"http://{LOOPBACK_HOST}:")
    assert server.port > 0
    server.start()
    server.wait_until_ready(timeout=3)
    assert server.thread_alive
    server.shutdown()
    server.shutdown()
    assert not server.thread_alive


def test_readiness_timeout_is_observable_and_cleanup_works(tmp_path):
    server = LocalServer(isolated_app(tmp_path))
    server.start()

    def unavailable(*_args, **_kwargs):
        raise URLError("blocked")

    with pytest.raises(TimeoutError):
        server.wait_until_ready(timeout=0.02, request=unavailable)
    server.shutdown()


def test_server_creation_uses_loopback_and_os_selected_port():
    calls = []
    fake_server = type("Server", (), {"server_port": 43210})()
    fake_server.serve_forever = lambda: None
    fake_server.shutdown = lambda: None
    fake_server.server_close = lambda: None

    def factory(host, port, application, threaded):
        calls.append((host, port, application, threaded))
        return fake_server

    application = object()
    server = LocalServer(application, server_factory=factory)

    assert calls == [("127.0.0.1", 0, application, True)]
    assert server.port == 43210


def test_single_instance_stale_file_second_rejection_and_release(tmp_path):
    path = tmp_path / "application.lock"
    path.write_text("stale")
    first = SingleInstanceLock(path)
    second = SingleInstanceLock(path)

    first.acquire()
    with pytest.raises(InstanceAlreadyRunning):
        second.acquire()
    first.release()
    second.acquire()
    second.release()


def test_locks_are_isolated_by_data_root(tmp_path):
    first = SingleInstanceLock(tmp_path / "one" / "application.lock")
    second = SingleInstanceLock(tmp_path / "two" / "application.lock")
    first.acquire()
    second.acquire()
    first.release()
    second.release()


def test_lifecycle_shutdown_is_repeatedly_safe(tmp_path):
    lock = SingleInstanceLock(tmp_path / "application.lock")
    lock.acquire()
    server = FakeServer(object())
    lifecycle = DesktopLifecycle(lock, __import__("logging").getLogger(), server)

    lifecycle.shutdown()
    lifecycle.shutdown()

    assert server.calls == ["shutdown"]
    replacement = SingleInstanceLock(lock.path)
    replacement.acquire()
    replacement.release()


def test_desktop_startup_order_window_configuration_and_shutdown(tmp_path):
    FakeServer.instances.clear()
    webview = FakeWebview()
    order = []

    def app_factory(config):
        order.append("database")
        assert config["DATA_ROOT"] == tmp_path.resolve()
        return object()

    class OrderedServer(FakeServer):
        def start(self):
            order.append("server")
            super().start()

        def wait_until_ready(self):
            order.append("ready")
            super().wait_until_ready()

    result = run_desktop(
        tmp_path,
        webview_module=webview,
        app_factory=app_factory,
        server_factory=OrderedServer,
    )

    assert result == 0
    assert order == ["database", "server", "ready"]
    assert len(webview.created) == 1
    title, options = webview.created[0]
    assert title == PRODUCT_NAME
    assert options["html"] == LOADING_HTML
    assert options["width"] == 1180 and options["height"] == 780
    assert options["min_size"] == (320, 560)
    assert options["resizable"] is True
    assert webview.window.loaded_urls == ["http://127.0.0.1:54321/"]
    assert OrderedServer.instances[-1].calls == ["start", "ready", "shutdown"]


def test_startup_failure_shows_friendly_html_and_releases_lock(tmp_path):
    webview = FakeWebview()

    def fail(_config):
        raise RuntimeError("customer/path/private.sqlite")

    assert run_desktop(tmp_path, webview_module=webview, app_factory=fail) == 0
    assert webview.window.loaded_html == [STARTUP_ERROR_HTML]
    assert "private.sqlite" not in STARTUP_ERROR_HTML
    replacement = SingleInstanceLock(tmp_path / "application.lock")
    replacement.acquire()
    replacement.release()


def test_second_desktop_launch_shows_message_without_server(tmp_path):
    held = SingleInstanceLock(tmp_path / "application.lock")
    held.acquire()
    webview = FakeWebview()
    FakeServer.instances.clear()
    try:
        assert run_desktop(
            tmp_path,
            webview_module=webview,
            server_factory=FakeServer,
        ) == 0
    finally:
        held.release()
    assert len(webview.created) == 1
    assert webview.created[0][1]["html"] == ALREADY_OPEN_HTML
    assert FakeServer.instances == []


def test_navigation_policy_rejects_remote_wrong_port_and_files():
    app_url = "http://127.0.0.1:4567/"
    assert allowed_primary_navigation(
        "http://127.0.0.1:4567/events/new", app_url
    )
    assert not allowed_primary_navigation("https://example.com", app_url)
    assert not allowed_primary_navigation("http://127.0.0.1:9999", app_url)
    assert not allowed_primary_navigation("file:///private/data", app_url)


def test_shell_paths_and_mutable_directories_stay_under_data_root(tmp_path):
    paths = desktop_data_paths(tmp_path)

    for path in (
        paths.database,
        paths.logs,
        paths.automatic_recovery,
        paths.staging,
        paths.shell_temporary,
        paths.safe_child(paths.root, "application.lock"),
    ):
        assert path.is_relative_to(tmp_path.resolve())


def test_loading_and_customer_templates_are_offline_only(client):
    assert "http://" not in LOADING_HTML
    assert "https://" not in LOADING_HTML
    for path in ("/", "/defaults", "/events/new", "/data-safety"):
        page = client.get(path).data.decode()
        assert "https://" not in page
        assert "//cdn." not in page


def test_import_has_no_server_or_window_side_effects():
    import app.desktop as desktop
    assert callable(desktop.main)
    assert callable(desktop.run_desktop)
