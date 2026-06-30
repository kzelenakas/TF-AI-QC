"""
Shared pytest fixtures.

Database: SQLite in-memory via create_all — no Alembic needed for tests.
Auth: override get_current_user with a factory that returns a known CurrentUser.
Storage: mock R2 so tests never touch network.
Ollama / Resend: patched to no-ops so tests don't need external services.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, patch

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.main import app
from app.models.base import Base  # declarative Base that all models inherit

# ── In-memory SQLite engine ───────────────────────────────────────────────────

SQLITE_URL = "sqlite:///:memory:"

_engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(autouse=True, scope="function")
def reset_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def db_session():
    """Yield a test database session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ── Auth helpers ──────────────────────────────────────────────────────────────

def make_user(role: str = "appraiser", user_id: str = "test-bubble-id", email: str = "test@truefootage.com") -> CurrentUser:
    return CurrentUser(user_id=user_id, role=role, email=email)


@pytest.fixture
def appraiser_user():
    return make_user(role="appraiser")


@pytest.fixture
def reviewer_user():
    return make_user(role="reviewer", user_id="reviewer-bubble-id", email="reviewer@truefootage.com")


@pytest.fixture
def admin_user():
    return make_user(role="admin", user_id="admin-bubble-id", email="admin@truefootage.com")


# ── TestClient factory ────────────────────────────────────────────────────────

def _make_client(current_user: CurrentUser) -> TestClient:
    """TestClient with DB + auth overrides."""
    def override_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    def override_auth():
        return current_user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_auth
    return TestClient(app)


@pytest.fixture
def client_appraiser(appraiser_user):
    client = _make_client(appraiser_user)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client_reviewer(reviewer_user):
    client = _make_client(reviewer_user)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client_admin(admin_user):
    client = _make_client(admin_user)
    yield client
    app.dependency_overrides.clear()


# ── Storage mock ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_r2_storage():
    """Patch R2 upload + presigned URL so tests never call AWS."""
    with patch("app.core.storage.upload_report", return_value="test/report.xml") as mock_upload, \
         patch("app.core.storage.get_presigned_url", return_value="https://r2.test/signed") as mock_url:
        yield {"upload": mock_upload, "url": mock_url}


# ── Ollama / AI mock ──────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_ollama():
    """Patch Ollama client so AI calls return a fixed score without network."""
    with patch(
        "app.services.ai.ollama_client.score_narrative",
        new_callable=AsyncMock,
        return_value={"score": 70, "flags": [], "reasoning": "mocked"},
    ):
        yield


# ── Notification / Bubble mocks ───────────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_side_effects():
    """No-op Bubble sync and Resend notifications in all tests."""
    with patch("app.services.integrations.bubble_client.sync_report_status", new_callable=AsyncMock, return_value=False), \
         patch("app.services.notifications.notify_qc_complete", new_callable=AsyncMock), \
         patch("app.services.notifications.notify_revision_requested", new_callable=AsyncMock), \
         patch("app.services.notifications.notify_approved", new_callable=AsyncMock):
        yield


# ── Minimal XML fixture (UAD 3.6 stub) ────────────────────────────────────────

MINIMAL_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<MESSAGE xmlns="http://www.mismo.org/residential/2009/schemas">
  <DEAL_SETS><DEAL_SET><DEALS><DEAL>
    <PARTIES>
      <PARTY SequenceNumber="1">
        <ROLES><ROLE><APPRAISER><LICENSE><LICENSE_NUMBER>AR123456</LICENSE_NUMBER><STATE_CODE>CA</STATE_CODE></LICENSE></APPRAISER></ROLE></ROLES>
      </PARTY>
    </PARTIES>
    <ASSETS><ASSET>
      <PROPERTY>
        <ADDRESS><StreetAddress>123 Main St</StreetAddress><City>Anytown</City><State>CA</State><PostalCode>90210</PostalCode></ADDRESS>
      </PROPERTY>
    </ASSET></ASSETS>
    <VALUATIONS><VALUATION>
      <APPRAISAL>
        <APPRAISAL_DETAIL>
          <EffectiveDate>2025-01-15</EffectiveDate>
          <ReportDate>2025-01-15</ReportDate>
          <AppraisedValue>450000</AppraisedValue>
          <ScopeOfWorkDescription>Full URAR appraisal with interior and exterior inspection of subject and three comparable sales within competitive market area.</ScopeOfWorkDescription>
          <IntendedUseDescription>Mortgage financing for purchase transaction</IntendedUseDescription>
          <IntendedUsersDescription>Lender and its successors</IntendedUsersDescription>
        </APPRAISAL_DETAIL>
      </APPRAISAL>
    </VALUATION></VALUATIONS>
  </DEAL></DEALS></DEAL_SET></DEAL_SETS>
</MESSAGE>
"""


@pytest.fixture
def minimal_xml_bytes():
    return MINIMAL_XML
