from video2srt.core import runtime


def test_headless_network_clients_disable_cli_progress(monkeypatch):
    monkeypatch.delenv("HF_HUB_DISABLE_PROGRESS_BARS", raising=False)
    runtime.configure_headless_network_clients()
    assert runtime.os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] == "1"


def test_system_certificates_are_skipped_outside_windows(monkeypatch):
    monkeypatch.setattr(runtime.sys, "platform", "linux")
    assert runtime.configure_system_certificates() is False


def test_system_certificates_are_injected_on_windows(monkeypatch):
    calls = []

    class FakeTruststore:
        @staticmethod
        def inject_into_ssl():
            calls.append(True)

    monkeypatch.setattr(runtime.sys, "platform", "win32")
    monkeypatch.setitem(runtime.sys.modules, "truststore", FakeTruststore)

    assert runtime.configure_system_certificates() is True
    assert calls == [True]
