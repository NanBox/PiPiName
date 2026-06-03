from fastapi.testclient import TestClient

from pipiname.api import create_app
from pipiname.cli import main
from pipiname.core import check_name, generate_names
from pipiname.models import GenerateOptions


def test_generate_shijing_returns_candidates():
    results = generate_names(GenerateOptions(last_name="林", source="shijing", limit=10))

    assert results
    assert len(results) <= 10
    assert all(item.full_name.startswith("林") for item in results)
    assert all(item.source_type == "shijing" for item in results)


def test_generate_filters_dislike_words():
    base = generate_names(GenerateOptions(last_name="林", source="shijing", limit=20))
    assert base
    dislike = base[0].first_char

    filtered = generate_names(
        GenerateOptions(last_name="林", source="shijing", dislike_words=(dislike,), limit=50)
    )

    assert all(dislike not in item.first_name for item in filtered)


def test_generate_normalizes_input_whitespace_and_dislike_words():
    results = generate_names(
        GenerateOptions(
            last_name=" 林 ",
            source="shijing",
            dislike_words=("马 侯",),
            limit=20,
        )
    )

    assert results
    assert all(item.full_name.startswith("林") for item in results)
    assert all("马" not in item.first_name and "侯" not in item.first_name for item in results)


def test_check_name_with_resource():
    result = check_name("周杰伦", with_resource=True)

    assert result.report.name == "周杰伦"
    assert result.resources


def test_api_endpoints():
    client = TestClient(create_app())

    assert "查看姓名" in client.get("/").text
    assert client.get("/api/health").json()["ok"] is True
    sources = client.get("/api/sources").json()
    assert any(item["source"] == "shijing" for item in sources["sources"])

    generated = client.post(
        "/api/names/generate",
        json={"last_name": "林", "source": "shijing", "limit": 5},
    )
    assert generated.status_code == 200
    assert generated.json()["count"] <= 5

    checked = client.post("/api/names/check", json={"name": "周杰伦", "with_resource": True})
    assert checked.status_code == 200
    assert checked.json()["report"]["name"] == "周杰伦"


def test_api_rejects_gender_without_validation():
    client = TestClient(create_app())

    response = client.post(
        "/api/names/generate",
        json={"last_name": "林", "source": "shijing", "gender": "男", "validate_name": False},
    )

    assert response.status_code == 400


def test_cli_generate_json_stdout(capsys):
    code = main([
        "generate",
        "--last-name",
        "林",
        "--source",
        "shijing",
        "--limit",
        "3",
        "--format",
        "json",
        "--output",
        "-",
    ])

    assert code == 0
    assert '"full_name"' in capsys.readouterr().out


def test_cli_default_output_follows_format(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    code = main([
        "generate",
        "--last-name",
        "林",
        "--source",
        "shijing",
        "--limit",
        "1",
        "--format",
        "json",
    ])

    assert code == 0
    assert (tmp_path / "names.json").exists()
    assert "names.json" in capsys.readouterr().out
