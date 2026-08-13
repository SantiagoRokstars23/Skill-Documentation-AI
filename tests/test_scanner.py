from analyzer.scanner import discover_java_files


def test_discovers_java_files_recursively(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "A.java").write_text("class A {}", encoding="utf-8")
    (tmp_path / "B.java").write_text("class B {}", encoding="utf-8")
    (tmp_path / "not-java.txt").write_text("ignore me", encoding="utf-8")

    files = discover_java_files(tmp_path)

    assert {f.name for f in files} == {"A.java", "B.java"}


def test_returns_empty_list_for_missing_directory(tmp_path):
    assert discover_java_files(tmp_path / "missing") == []
