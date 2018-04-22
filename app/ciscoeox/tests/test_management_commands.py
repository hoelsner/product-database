import pytest
from io import StringIO
from django.core.cache import cache
from django.core.management import call_command, CommandError
from app.ciscoeox import tasks


class TaskResultMock:
    id = "MOCK_TASK_ID"


class TestInitialImportCommand:
    def test_call_with_disabled_cisco_api(self):
        expected_value = "Please configure the Cisco EoX API in the settings prior running this task"

        out = StringIO()
        with pytest.raises(CommandError) as ex:
            call_command("initialimport", "2018", stdout=out)

        assert ex.match(expected_value)

    @pytest.mark.usefixtures("enable_cisco_api")
    def test_call_with_enabled_cisco_api(self, monkeypatch):
        expected_value = "Task successful started...\n"

        monkeypatch.setattr(
            tasks.initial_sync_with_cisco_eox_api,
            "apply_async",
            lambda *args, **kwargs: TaskResultMock()
        )

        out = StringIO()
        call_command("initialimport", "2018", stdout=out)
        assert out.getvalue() == expected_value

    @pytest.mark.usefixtures("enable_cisco_api")
    def test_call_already_scheduled(self, monkeypatch):
        expected_value = "initial import already running..."

        monkeypatch.setattr(
            tasks.initial_sync_with_cisco_eox_api,
            "apply_async",
            lambda *args, **kwargs: TaskResultMock()
        )

        cache.set("CISCO_EOX_INITIAL_SYN_IN_PROGRESS", "SOMETHING", 60 * 60 * 48)
        cache.set("CISCO_EOX_INITIAL_SYN_LAST_RUN", "SOMETHING", 60 * 60 * 48)

        out = StringIO()

        with pytest.raises(CommandError) as ex:
            call_command("initialimport", "2018", stdout=out)

        assert ex.match(expected_value)


class TestInitialImportStatusCommand:
    def test_initial_import_status_command(self):
        expected_value = "Task ID not found, the initial import was not executed or the results are already deleted"

        out = StringIO()
        call_command("initialimportstatus", stdout=out)
        assert expected_value in out.getvalue()
