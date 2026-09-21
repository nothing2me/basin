from pathlib import Path

import scripts.build_exe as build_exe
import scripts.build_offline_bundle as bundle


def test_copy_application_files_includes_every_runtime_support_file(tmp_path, monkeypatch):
    source = tmp_path / "source"
    output = tmp_path / "bundle"
    source.mkdir()

    for relative in bundle.ROOT_RUNTIME_FILES + bundle.RUNTIME_SUPPORT_FILES:
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"fixture for {relative}\n", encoding="utf-8")

    (source / "BASIN.exe").write_bytes(b"fixture executable")
    for directory in bundle.RUNTIME_DIRECTORIES:
        path = source / directory
        path.mkdir(parents=True, exist_ok=True)
        (path / "fixture.txt").write_text("fixture\n", encoding="utf-8")

    monkeypatch.setattr(bundle, "ROOT", source)
    monkeypatch.setattr(bundle, "BUNDLE_DIR", output)
    bundle.copy_application_files()

    expected = ["BASIN.exe", *bundle.ROOT_RUNTIME_FILES, *bundle.RUNTIME_SUPPORT_FILES]
    assert all((output / relative).is_file() for relative in expected)
    assert not (output / "models" / "weights.gguf").exists()


def test_copy_application_files_fails_when_support_file_is_missing(tmp_path, monkeypatch):
    source = tmp_path / "source"
    output = tmp_path / "bundle"
    source.mkdir()
    (source / "BASIN.exe").write_bytes(b"fixture executable")

    for relative in bundle.ROOT_RUNTIME_FILES + bundle.RUNTIME_SUPPORT_FILES[:-1]:
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
    for directory in bundle.RUNTIME_DIRECTORIES:
        (source / directory).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(bundle, "ROOT", source)
    monkeypatch.setattr(bundle, "BUNDLE_DIR", output)

    try:
        bundle.copy_application_files()
    except FileNotFoundError as exc:
        assert "models\\manifest.json" in str(exc) or "models/manifest.json" in str(exc)
    else:
        raise AssertionError("Missing runtime support file did not fail the build")


def test_copy_application_files_uses_staged_release_launcher(tmp_path, monkeypatch):
    source = tmp_path / "source"
    output = tmp_path / "bundle"
    source.mkdir()

    for relative in bundle.ROOT_RUNTIME_FILES + bundle.RUNTIME_SUPPORT_FILES:
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
    for directory in bundle.RUNTIME_DIRECTORIES:
        (source / directory).mkdir(parents=True, exist_ok=True)

    staged_launcher = tmp_path / "BASIN-release.exe"
    staged_launcher.write_bytes(b"fresh release launcher")
    (source / "BASIN.exe").write_bytes(b"stale locked launcher")

    monkeypatch.setattr(bundle, "ROOT", source)
    monkeypatch.setattr(bundle, "BUNDLE_DIR", output)
    monkeypatch.setenv("BASIN_LAUNCHER_PATH", str(staged_launcher))

    bundle.copy_application_files()

    assert (output / "BASIN.exe").read_bytes() == b"fresh release launcher"


def test_build_exe_honors_release_output_name(monkeypatch):
    monkeypatch.setenv("BASIN_BUILD_NAME", "BASIN-release")
    assert build_exe.output_name() == "BASIN-release"
