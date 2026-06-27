from __future__ import annotations

import os

os.environ.setdefault("MOCK_MODE", "true")
os.environ.setdefault("ENABLE_WEB_SEARCH", "true")
os.environ.setdefault("ENABLE_VIRUSTOTAL", "false")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-secret")
os.environ.setdefault("OPENAI_MODEL_FAST", "fast-model")
os.environ.setdefault("OPENAI_MODEL_EXPERT", "expert-model")
os.environ.setdefault("OPENAI_MODEL_JUDGE", "judge-model")
os.environ.setdefault("OPENAI_MODEL_REPORT", "report-model")
os.environ.setdefault("TAVILY_API_KEY", "test-tavily-secret")
os.environ.setdefault("VIRUSTOTAL_API_KEY", "test-vt-secret")
