import json

from scripts import populate_ogm_repos


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body
        self.text = json.dumps(body)

    def json(self):
        return self._body


def setup_function():
    populate_ogm_repos._BAD_GITHUB_TOKEN_WARNING_SHOWN = False
    populate_ogm_repos._REJECTED_GITHUB_TOKENS.clear()


def test_list_org_repos_retries_without_rejected_token(monkeypatch, capsys):
    responses = [
        FakeResponse(401, {"message": "Bad credentials"}),
        FakeResponse(200, [{"name": "edu.example"}]),
        FakeResponse(200, []),
    ]
    calls = []

    def fake_get(url, headers, params, timeout):
        calls.append({"url": url, "headers": headers, "params": params, "timeout": timeout})
        return responses.pop(0)

    monkeypatch.setattr(populate_ogm_repos.requests, "get", fake_get)

    repos = populate_ogm_repos.list_org_repos("OpenGeoMetadata", "bad-token")

    assert repos == [{"name": "edu.example"}]
    assert calls[0]["headers"]["Authorization"] == "Bearer bad-token"
    assert "Authorization" not in calls[1]["headers"]
    assert "Authorization" not in calls[2]["headers"]
    assert "configured GitHub token was rejected with 401" in capsys.readouterr().err


def test_repo_has_metadata_aardvark_retries_without_rejected_token(monkeypatch):
    responses = [
        FakeResponse(401, {"message": "Bad credentials"}),
        FakeResponse(200, [{"name": "geoblacklight.json"}]),
    ]
    calls = []

    def fake_get(url, headers, params, timeout):
        calls.append({"url": url, "headers": headers, "params": params, "timeout": timeout})
        return responses.pop(0)

    monkeypatch.setattr(populate_ogm_repos.requests, "get", fake_get)

    assert (
        populate_ogm_repos.repo_has_metadata_aardvark(
            "OpenGeoMetadata", "edu.example", "main", "bad-token"
        )
        is True
    )
    assert calls[0]["headers"]["Authorization"] == "Bearer bad-token"
    assert "Authorization" not in calls[1]["headers"]
