"""
Tests for ServiceResult — the generic result wrapper used across all service
layer operations.  No external dependencies, no mocks needed.
"""
import pytest
from src.services.result import ServiceResult


class TestServiceResultOk:
    def test_ok_sets_success_true(self):
        result = ServiceResult.ok()
        assert result.success is True

    def test_ok_with_no_data_has_none_data(self):
        result = ServiceResult.ok()
        assert result.data is None

    def test_ok_carries_data_payload(self):
        result = ServiceResult.ok(data=[1, 2, 3])
        assert result.data == [1, 2, 3]

    def test_ok_has_no_error(self):
        result = ServiceResult.ok("some data")
        assert result.error is None

    def test_ok_is_not_not_found(self):
        result = ServiceResult.ok()
        assert result.is_not_found is False

    def test_ok_is_truthy(self):
        assert bool(ServiceResult.ok()) is True


class TestServiceResultFail:
    def test_fail_sets_success_false(self):
        result = ServiceResult.fail("something went wrong")
        assert result.success is False

    def test_fail_stores_error_message(self):
        result = ServiceResult.fail("db timeout")
        assert result.error == "db timeout"

    def test_fail_has_no_data(self):
        result = ServiceResult.fail("error")
        assert result.data is None

    def test_fail_is_not_not_found(self):
        result = ServiceResult.fail("error")
        assert result.is_not_found is False

    def test_fail_is_falsy(self):
        assert bool(ServiceResult.fail("error")) is False


class TestServiceResultNotFound:
    def test_not_found_sets_success_false(self):
        result = ServiceResult.not_found("record missing")
        assert result.success is False

    def test_not_found_sets_is_not_found_true(self):
        result = ServiceResult.not_found("record missing")
        assert result.is_not_found is True

    def test_not_found_stores_message_in_error(self):
        result = ServiceResult.not_found("no member with code X")
        assert result.error == "no member with code X"

    def test_not_found_has_no_data(self):
        result = ServiceResult.not_found("missing")
        assert result.data is None

    def test_not_found_is_falsy(self):
        assert bool(ServiceResult.not_found("missing")) is False


class TestServiceResultBoolDunder:
    def test_truthy_on_success(self):
        assert ServiceResult(success=True)

    def test_falsy_on_failure(self):
        assert not ServiceResult(success=False)

    def test_usable_in_if_statement(self):
        result = ServiceResult.ok("data")
        if result:
            passed = True
        else:
            passed = False  # pragma: no cover
        assert passed
