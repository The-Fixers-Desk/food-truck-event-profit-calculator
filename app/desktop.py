"""Controllable localhost server and native desktop-shell orchestration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import shutil
import threading
import time
from typing import Callable
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from werkzeug.serving import BaseWSGIServer, make_server

from app import create_app
from app.data_paths import ApplicationDataPaths


PRODUCT_NAME = "Food Truck Event Profit Calculator"
LOOPBACK_HOST = "127.0.0.1"
LOADING_HTML = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width"><title>Starting</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#f6f3ed;color:#18232d;font:16px system-ui,sans-serif}main{text-align:center;padding:2rem}.spinner{width:2rem;height:2rem;margin:1.5rem auto;border:.25rem solid #d9d7d0;border-top-color:#a75726;border-radius:50%;animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}@media(prefers-reduced-motion:reduce){.spinner{animation:none}}</style>
</head><body><main><h1>Food Truck Event Profit Calculator</h1>
<p>Starting your event calculator&hellip;</p><div class="spinner" aria-hidden="true"></div></main></body></html>"""
STARTUP_ERROR_HTML = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width"><title>Could not start</title>
<style>body{margin:0;padding:2rem;background:#f6f3ed;color:#18232d;font:16px system-ui,sans-serif}main{max-width:38rem;margin:auto}</style></head>
<body><main><h1>The application could not start</h1><p>Your saved data was not intentionally deleted. Close and reopen the application. If the problem continues, use the troubleshooting information provided with the application.</p></main></body></html>"""
ALREADY_OPEN_MESSAGE = (
    "The application is already open. Return to the existing application "
    "window to continue."
)
STARTUP_ERROR_MESSAGE = (
    "The application could not start. Your saved data was not intentionally "
    "deleted. Close and reopen the application. If the problem continues, "
    "use the troubleshooting information provided with the application."
)


class InstanceAlreadyRunning(RuntimeError):
    """Raised when another process owns the application instance lock."""


class SingleInstanceLock:
    """Cross-platform advisory lock whose file lives under the data root."""

    def __init__(self, path: Path):
        self.path = path.resolve()
        self._file = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        try:
            if _try_lock(handle):
                self._file = handle
                return
        except Exception:
            handle.close()
            raise
        handle.close()
        raise InstanceAlreadyRunning()

    def release(self) -> None:
        if self._file is None:
            return
        try:
            _unlock(self._file)
        finally:
            self._file.close()
            self._file = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *_):
        self.release()


def _try_lock(handle) -> bool:
    if __import__("os").name == "nt":
        import msvcrt
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True
    import fcntl
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _unlock(handle) -> None:
    if __import__("os").name == "nt":
        import msvcrt
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
    else:
        import fcntl
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class LocalServer:
    """Managed loopback-only Werkzeug server using an OS-selected port."""

    def __init__(self, application, server_factory=make_server):
        self._server: BaseWSGIServer = server_factory(
            LOOPBACK_HOST, 0, application, threaded=True
        )
        self.port = self._server.server_port
        self.url = f"http://{LOOPBACK_HOST}:{self.port}/"
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="food-truck-calculator-server",
            daemon=False,
        )
        self._started = False
        self._shutdown = False

    def start(self) -> None:
        if not self._started:
            self._thread.start()
            self._started = True

    def wait_until_ready(
        self,
        timeout: float = 10,
        request: Callable = urlopen,
    ) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._started and not self._thread.is_alive():
                raise RuntimeError("Local server stopped during startup.")
            try:
                with request(self.url, timeout=0.25) as response:
                    if response.status < 500:
                        return
            except (OSError, URLError):
                time.sleep(0.05)
        raise TimeoutError("Local server readiness timed out.")

    def shutdown(self, timeout: float = 5) -> None:
        if self._shutdown:
            return
        self._shutdown = True
        self._server.shutdown()
        self._server.server_close()
        if self._started and self._thread.is_alive():
            self._thread.join(timeout)

    @property
    def thread_alive(self) -> bool:
        return self._thread.is_alive()


def allowed_primary_navigation(url: str, application_url: str) -> bool:
    """Allow only the exact loopback application origin in the main window."""
    target = urlparse(url)
    application = urlparse(application_url)
    return (
        target.scheme in {"http", "https"}
        and target.hostname == LOOPBACK_HOST
        and (target.scheme, target.hostname, target.port)
        == (application.scheme, application.hostname, application.port)
    )


def enforce_primary_navigation(
    window,
    application_url: str,
    *,
    external_opener: Callable[[str], object] | None = None,
) -> bool:
    """Keep the primary window local and hand deliberate web links to the OS."""
    current_url = window.get_current_url()
    if not current_url or allowed_primary_navigation(
        current_url, application_url
    ):
        return True
    if urlparse(current_url).scheme in {"http", "https"}:
        opener = external_opener or __import__("webbrowser").open
        opener(current_url)
    window.load_url(application_url)
    return False


def show_native_message(title: str, message: str) -> None:
    """Show a brief OS dialog without creating another application webview."""
    if os.name == "nt":
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, title, 0x40)
        return
    import tkinter
    from tkinter import messagebox

    root = tkinter.Tk()
    root.withdraw()
    try:
        messagebox.showinfo(title, message, parent=root)
    finally:
        root.destroy()


def clean_shell_temporary(
    paths: ApplicationDataPaths, logger: logging.Logger
) -> None:
    """Remove only shell-owned temporary children beneath the data root."""
    try:
        temporary = paths.shell_temporary.resolve()
        temporary.relative_to(paths.root.resolve())
        for child in temporary.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
    except (OSError, ValueError):
        logger.warning("Desktop shell temporary-file cleanup failed.", exc_info=True)


@dataclass
class DesktopLifecycle:
    """Own partial-startup cleanup, server shutdown and lock release."""

    lock: SingleInstanceLock
    logger: logging.Logger
    server: LocalServer | None = None
    paths: ApplicationDataPaths | None = None
    shutting_down: bool = False

    def shutdown(self) -> None:
        if self.shutting_down:
            return
        self.shutting_down = True
        try:
            if self.server is not None:
                self.server.shutdown()
                if self.server.thread_alive:
                    self.logger.error("Desktop server thread exceeded shutdown timeout.")
        finally:
            if self.paths is not None:
                clean_shell_temporary(self.paths, self.logger)
            self.lock.release()


def desktop_data_paths(data_root: Path | None = None) -> ApplicationDataPaths:
    """Resolve development-compatible mutable paths for the desktop shell."""
    root = (data_root or Path(__file__).resolve().parents[1] / "data").resolve()
    return ApplicationDataPaths.from_config(
        {"DATA_ROOT": root, "DATABASE": root / "app.db"}
    )


def run_desktop(
    data_root: Path | None = None,
    *,
    webview_module=None,
    app_factory=create_app,
    server_factory=LocalServer,
    message_handler: Callable[[str, str], None] = show_native_message,
    external_opener: Callable[[str], object] | None = None,
) -> int:
    """Explicit production desktop entrypoint; importing has no side effects."""
    if webview_module is None:
        import webview as webview_module
    try:
        paths = desktop_data_paths(data_root)
        lock = SingleInstanceLock(paths.safe_child(paths.root, "application.lock"))
    except Exception:
        logging.getLogger("desktop").exception(
            "Desktop application-data initialization failed."
        )
        message_handler(PRODUCT_NAME, STARTUP_ERROR_MESSAGE)
        return 1
    try:
        lock.acquire()
    except InstanceAlreadyRunning:
        message_handler(PRODUCT_NAME, ALREADY_OPEN_MESSAGE)
        return 0
    except Exception:
        logging.getLogger("desktop").exception("Desktop instance lock failed.")
        message_handler(PRODUCT_NAME, STARTUP_ERROR_MESSAGE)
        return 1

    lifecycle = DesktopLifecycle(
        lock, logging.getLogger("desktop"), paths=paths
    )
    try:
        window = webview_module.create_window(
            PRODUCT_NAME,
            html=LOADING_HTML,
            width=1180,
            height=780,
            min_size=(320, 560),
            resizable=True,
        )
        window.events.closed += lifecycle.shutdown
    except Exception:
        lifecycle.logger.exception("Desktop window creation failed.")
        lifecycle.shutdown()
        message_handler(PRODUCT_NAME, STARTUP_ERROR_MESSAGE)
        return 1

    startup_failed = False

    def startup() -> None:
        nonlocal startup_failed
        try:
            application = app_factory(
                {"DATA_ROOT": paths.root, "DATABASE": paths.database}
            )
            server = server_factory(application)
            lifecycle.server = server
            server.start()
            server.wait_until_ready()
            if hasattr(window.events, "before_load"):
                window.events.before_load += lambda active_window=window: (
                    enforce_primary_navigation(
                        active_window,
                        server.url,
                        external_opener=external_opener,
                    )
                )
            window.load_url(server.url)
        except Exception:
            startup_failed = True
            lifecycle.logger.exception("Desktop application startup failed.")
            if hasattr(window, "load_html"):
                window.load_html(STARTUP_ERROR_HTML)
            lifecycle.shutdown()

    try:
        webview_module.start(startup)
    finally:
        lifecycle.shutdown()
    return 1 if startup_failed else 0


def main() -> int:
    return run_desktop()


if __name__ == "__main__":
    raise SystemExit(main())
