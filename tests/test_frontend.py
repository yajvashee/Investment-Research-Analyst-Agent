import httpx
import pytest
from app.frontend.client import submit_research

class FakeClient:
    def post(self, _url, json):
        assert json["question"] == "Test question"
        return httpx.Response(200, json={"status": "success", "answer": "Answer"}, request=httpx.Request("POST", "http://test/research"))

def test_submit_research_returns_backend_response():
    assert submit_research({"question": "Test question"}, FakeClient())["answer"] == "Answer"

def test_submit_research_rejects_invalid_response():
    class BadClient:
        def post(self, *_args, **_kwargs): return httpx.Response(200, json={"status": "success"}, request=httpx.Request("POST", "http://test"))
    with pytest.raises(RuntimeError, match="unexpected response"):
        submit_research({"question": "Test question"}, BadClient())
