import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.audit import AuditEvent
from app.services.audit_service import AuditService

pytestmark = pytest.mark.unit


class TestAuditLog:
    @pytest.fixture
    def service(self, mock_db):
        return AuditService(mock_db)

    @pytest.mark.asyncio
    async def test_log_creates_event(self, service, mock_db, tenant_id, user_id):
        await service.log(
            "user.login",
            tenant_id=tenant_id,
            user_id=user_id,
            ip_address="10.0.0.1",
        )
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()
        added_obj = mock_db.add.call_args[0][0]
        assert isinstance(added_obj, AuditEvent)
        assert added_obj.action == "user.login"
        assert added_obj.tenant_id == tenant_id
        assert added_obj.user_id == user_id
        assert added_obj.ip_address == "10.0.0.1"

    @pytest.mark.asyncio
    async def test_log_nullable_fields(self, service, mock_db):
        await service.log("system.startup")
        added_obj = mock_db.add.call_args[0][0]
        assert added_obj.tenant_id is None
        assert added_obj.user_id is None
        assert added_obj.resource_type is None
        assert added_obj.resource_id is None
        assert added_obj.details is None

    @pytest.mark.asyncio
    async def test_log_with_resource(self, service, mock_db, tenant_id, user_id):
        rid = uuid.uuid4()
        await service.log(
            "evidence.upload",
            tenant_id=tenant_id,
            user_id=user_id,
            resource_type="evidence",
            resource_id=rid,
            details={"filename": "soc2_report.pdf"},
        )
        added_obj = mock_db.add.call_args[0][0]
        assert added_obj.resource_type == "evidence"
        assert added_obj.resource_id == rid
        assert added_obj.details == {"filename": "soc2_report.pdf"}

    @pytest.mark.asyncio
    async def test_log_with_user_agent(self, service, mock_db, tenant_id):
        await service.log(
            "user.login",
            tenant_id=tenant_id,
            user_agent="Mozilla/5.0",
        )
        added_obj = mock_db.add.call_args[0][0]
        assert added_obj.user_agent == "Mozilla/5.0"


class TestAuditQuery:
    @pytest.fixture
    def service(self, mock_db):
        return AuditService(mock_db)

    def _setup_query_mock(self, mock_db, events, total):
        count_result = MagicMock()
        count_result.scalar_one.return_value = total

        rows_result = MagicMock()
        rows_result.scalars.return_value.all.return_value = events

        mock_db.execute = AsyncMock(side_effect=[count_result, rows_result])

    @pytest.mark.asyncio
    async def test_query_returns_events_and_total(self, service, mock_db, tenant_id):
        mock_events = [MagicMock(spec=AuditEvent), MagicMock(spec=AuditEvent)]
        self._setup_query_mock(mock_db, mock_events, 2)

        events, total = await service.query(tenant_id)
        assert len(events) == 2
        assert total == 2
        assert mock_db.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_query_empty_result(self, service, mock_db, tenant_id):
        self._setup_query_mock(mock_db, [], 0)

        events, total = await service.query(tenant_id)
        assert events == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_query_respects_limit_and_offset(self, service, mock_db, tenant_id):
        self._setup_query_mock(mock_db, [MagicMock()], 10)

        events, total = await service.query(tenant_id, limit=1, offset=5)
        assert total == 10
        assert len(events) == 1
