"""
Tests for PaymentService.

All database interactions are isolated by patching the global `db_manager`
singleton that `payment_service` imports at module level.

Patch target: 'src.services.payment_service.db_manager'
"""
import pytest
from unittest.mock import patch
from datetime import datetime, date

from src.services.payment_service import PaymentService
from src.models.enums import PaymentMethod, PaymentStatus


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

def make_payment_row(**kwargs) -> dict:
    """Factory for a raw DB row matching the payments table schema (with member join columns)."""
    defaults = dict(
        id="pay-001",
        member_id="mem-001",
        membership_id="ms-001",
        amount=500.00,
        payment_method="cash",
        payment_date="2026-04-25T10:00:00+00:00",
        status="completed",
        reference_number="REF-001",
        notes="Monthly payment",
        created_at="2026-04-25T10:00:00+00:00",
        created_by="user-001",
        member_code="GYM001",
        first_name="John",
        last_name="Doe",
    )
    defaults.update(kwargs)
    return defaults


def make_member_row(**kwargs) -> dict:
    """Factory for a raw DB row matching the members table schema."""
    defaults = dict(
        id="mem-001",
        member_code="GYM001",
        first_name="John",
        last_name="Doe",
        is_active=True,
    )
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# _row_to_payment  (pure static)
# ---------------------------------------------------------------------------

class TestRowToPayment:
    def setup_method(self):
        self.svc = PaymentService()

    def test_basic_fields_are_mapped(self):
        pay = self.svc._row_to_payment(make_payment_row())
        assert pay.id == "pay-001"
        assert pay.member_id == "mem-001"
        assert pay.amount == 500.00
        assert pay.payment_method == PaymentMethod.CASH
        assert pay.status == PaymentStatus.COMPLETED

    def test_amount_is_converted_to_float(self):
        row = make_payment_row(amount=750)
        pay = self.svc._row_to_payment(row)
        assert pay.amount == 750.0
        assert isinstance(pay.amount, float)

    def test_payment_method_is_converted_to_enum(self):
        pay = self.svc._row_to_payment(make_payment_row(payment_method="card"))
        assert pay.payment_method == PaymentMethod.CARD

    def test_status_is_converted_to_enum(self):
        pay = self.svc._row_to_payment(make_payment_row(status="pending"))
        assert pay.status == PaymentStatus.PENDING

    def test_payment_date_is_parsed_correctly(self):
        pay = self.svc._row_to_payment(make_payment_row())
        assert isinstance(pay.payment_date, datetime)
        assert pay.payment_date.year == 2026
        assert pay.payment_date.month == 4
        assert pay.payment_date.day == 25

    def test_populates_member_relation(self):
        pay = self.svc._row_to_payment(make_payment_row())
        assert pay.member is not None
        assert pay.member.member_code == "GYM001"
        assert pay.member.full_name == "John Doe"

    def test_member_id_assigned_to_member_object(self):
        pay = self.svc._row_to_payment(make_payment_row())
        assert pay.member.id == "mem-001"

    def test_no_member_relation_stays_none(self):
        row = make_payment_row(member_code=None)
        pay = self.svc._row_to_payment(row)
        assert pay.member is None

    def test_reference_number_is_preserved(self):
        pay = self.svc._row_to_payment(make_payment_row())
        assert pay.reference_number == "REF-001"

    def test_membership_id_is_preserved(self):
        pay = self.svc._row_to_payment(make_payment_row())
        assert pay.membership_id == "ms-001"

    def test_invalid_payment_date_falls_back_to_now(self):
        row = make_payment_row(payment_date="not-a-date")
        pay = self.svc._row_to_payment(row)
        assert isinstance(pay.payment_date, datetime)

    def test_datetime_instance_is_accepted_directly(self):
        dt = datetime(2026, 4, 25, 10, 0, 0)
        row = make_payment_row(payment_date=dt)
        pay = self.svc._row_to_payment(row)
        assert pay.payment_date == dt


# ---------------------------------------------------------------------------
# _validate_payment  (pure static)
# ---------------------------------------------------------------------------

class TestValidatePayment:
    def test_valid_payment_returns_none(self):
        from src.models import Payment as PaymentModel
        payment = PaymentModel(member_id="mem-001", amount=500.00)
        result = PaymentService._validate_payment(payment)
        assert result is None

    def test_empty_member_id_returns_error(self):
        from src.models import Payment as PaymentModel
        payment = PaymentModel(member_id="", amount=500.00)
        result = PaymentService._validate_payment(payment)
        assert result is not None
        assert "Member" in result

    def test_zero_amount_returns_error(self):
        from src.models import Payment as PaymentModel
        payment = PaymentModel(member_id="mem-001", amount=0.0)
        result = PaymentService._validate_payment(payment)
        assert result is not None
        assert "Amount" in result

    def test_negative_amount_returns_error(self):
        from src.models import Payment as PaymentModel
        payment = PaymentModel(member_id="mem-001", amount=-100.0)
        result = PaymentService._validate_payment(payment)
        assert result is not None
        assert "Amount" in result


# ---------------------------------------------------------------------------
# _payment_to_row  (pure static)
# ---------------------------------------------------------------------------

class TestPaymentToRow:
    def test_all_fields_are_included(self):
        from src.models import Payment as PaymentModel
        payment = PaymentModel(
            member_id="mem-001",
            membership_id="ms-001",
            amount=500.00,
            payment_method=PaymentMethod.CARD,
            payment_date=datetime(2026, 4, 25, 10, 0, 0),
            status=PaymentStatus.COMPLETED,
            reference_number="REF-001",
            notes="Test",
        )
        row = PaymentService._payment_to_row(payment)
        assert row['member_id'] == "mem-001"
        assert row['membership_id'] == "ms-001"
        assert row['amount'] == 500.00
        assert row['payment_method'] == "card"
        assert row['status'] == "completed"
        assert row['reference_number'] == "REF-001"
        assert row['notes'] == "Test"
        assert "payment_date" in row


# ---------------------------------------------------------------------------
# get_payments
# ---------------------------------------------------------------------------

class TestGetPayments:
    def setup_method(self):
        self.svc = PaymentService()

    @patch("src.services.payment_service.db_manager")
    def test_returns_payments_on_success(self, mock_db):
        mock_db.select.return_value = [make_payment_row()]
        result = self.svc.get_payments()
        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0].member.full_name == "John Doe"

    @patch("src.services.payment_service.db_manager")
    def test_returns_empty_list_when_no_records(self, mock_db):
        mock_db.select.return_value = []
        result = self.svc.get_payments()
        assert result.success is True
        assert result.data == []

    @patch("src.services.payment_service.db_manager")
    def test_filters_by_status(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_payments(status=PaymentStatus.PENDING)
        call_kwargs = mock_db.select.call_args.kwargs
        assert call_kwargs['filters'] == {'status': 'pending'}

    @patch("src.services.payment_service.db_manager")
    def test_filters_by_payment_method(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_payments(payment_method=PaymentMethod.CARD)
        call_kwargs = mock_db.select.call_args.kwargs
        assert call_kwargs['filters'] == {'payment_method': 'card'}

    @patch("src.services.payment_service.db_manager")
    def test_filters_by_both_status_and_method(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_payments(status=PaymentStatus.COMPLETED, payment_method=PaymentMethod.CASH)
        call_kwargs = mock_db.select.call_args.kwargs
        assert call_kwargs['filters'] == {'status': 'completed', 'payment_method': 'cash'}

    @patch("src.services.payment_service.db_manager")
    def test_uses_date_range_when_dates_provided(self, mock_db):
        mock_db.select_range.return_value = []
        self.svc.get_payments(date_from=date(2026, 4, 1), date_to=date(2026, 4, 30))
        mock_db.select_range.assert_called_once()
        call_kwargs = mock_db.select_range.call_args.kwargs
        assert call_kwargs['start'] == '2026-04-01'
        assert call_kwargs['end'] == '2026-04-30'

    @patch("src.services.payment_service.db_manager")
    def test_queries_payments_table_with_member_join(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_payments()
        call_kwargs = mock_db.select.call_args.kwargs
        assert call_kwargs['table'] == 'payments'
        assert 'members.first_name' in call_kwargs['columns']
        assert call_kwargs['joins'] is not None

    @patch("src.services.payment_service.db_manager")
    def test_orders_by_payment_date(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_payments()
        call_kwargs = mock_db.select.call_args.kwargs
        assert call_kwargs['order_by'] == 'payment_date'

    @patch("src.services.payment_service.db_manager")
    def test_filters_by_search_term_in_python(self, mock_db):
        mock_db.select.return_value = [
            make_payment_row(id="pay-001", first_name="John"),
            make_payment_row(id="pay-002", member_id="mem-002", member_code="GYM002", first_name="Jane", last_name="Smith"),
        ]
        result = self.svc.get_payments(search_term="Jane")
        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0].id == "pay-002"

    @patch("src.services.payment_service.db_manager")
    def test_search_term_matches_by_member_code(self, mock_db):
        mock_db.select.return_value = [
            make_payment_row(),
        ]
        result = self.svc.get_payments(search_term="GYM001")
        assert result.success is True
        assert len(result.data) == 1

    @patch("src.services.payment_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.select.side_effect = Exception("connection lost")
        result = self.svc.get_payments()
        assert result.success is False
        assert result.error is not None


# ---------------------------------------------------------------------------
# get_payments_by_member
# ---------------------------------------------------------------------------

class TestGetPaymentsByMember:
    def setup_method(self):
        self.svc = PaymentService()

    @patch("src.services.payment_service.db_manager")
    def test_returns_payments_for_member(self, mock_db):
        mock_db.select.return_value = [make_payment_row()]
        result = self.svc.get_payments_by_member("mem-001")
        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0].member_id == "mem-001"

    @patch("src.services.payment_service.db_manager")
    def test_filters_by_member_id(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_payments_by_member("mem-001")
        call_kwargs = mock_db.select.call_args.kwargs
        assert call_kwargs['filters'] == {'member_id': 'mem-001'}

    @patch("src.services.payment_service.db_manager")
    def test_returns_empty_list_when_no_payments(self, mock_db):
        mock_db.select.return_value = []
        result = self.svc.get_payments_by_member("mem-999")
        assert result.success is True
        assert result.data == []

    @patch("src.services.payment_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.select.side_effect = Exception("db error")
        result = self.svc.get_payments_by_member("mem-001")
        assert result.success is False


# ---------------------------------------------------------------------------
# create_payment
# ---------------------------------------------------------------------------

class TestCreatePayment:
    def setup_method(self):
        self.svc = PaymentService()

    @patch("src.services.payment_service.db_manager")
    def test_creates_payment_successfully(self, mock_db):
        mock_db.insert.return_value = make_payment_row()
        from src.models import Payment as PaymentModel
        payment = PaymentModel(member_id="mem-001", amount=500.00)
        result = self.svc.create_payment(payment, "user-001")
        assert result.success is True
        assert result.data.id == "pay-001"

    @patch("src.services.payment_service.db_manager")
    def test_validation_error_blocks_db_call(self, mock_db):
        from src.models import Payment as PaymentModel
        payment = PaymentModel(member_id="", amount=0.0)
        result = self.svc.create_payment(payment)
        assert result.success is False
        mock_db.insert.assert_not_called()

    @patch("src.services.payment_service.db_manager")
    def test_calls_insert_with_correct_table(self, mock_db):
        mock_db.insert.return_value = make_payment_row()
        from src.models import Payment as PaymentModel
        payment = PaymentModel(member_id="mem-001", amount=500.00)
        self.svc.create_payment(payment)
        assert mock_db.insert.call_args.args[0] == "payments"

    @patch("src.services.payment_service.db_manager")
    def test_insert_payload_contains_required_fields(self, mock_db):
        mock_db.insert.return_value = make_payment_row()
        from src.models import Payment as PaymentModel
        payment = PaymentModel(
            member_id="mem-001",
            amount=500.00,
            payment_method=PaymentMethod.CARD,
            notes="Test payment",
        )
        self.svc.create_payment(payment, "user-001")
        payload = mock_db.insert.call_args.args[1]
        assert payload['member_id'] == "mem-001"
        assert payload['amount'] == 500.00
        assert payload['payment_method'] == "card"
        assert payload['status'] == "completed"
        assert payload['created_by'] == "user-001"
        assert payload['notes'] == "Test payment"

    @patch("src.services.payment_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.insert.side_effect = Exception("insert failed")
        from src.models import Payment as PaymentModel
        payment = PaymentModel(member_id="mem-001", amount=500.00)
        result = self.svc.create_payment(payment)
        assert result.success is False


# ---------------------------------------------------------------------------
# update_payment
# ---------------------------------------------------------------------------

class TestUpdatePayment:
    def setup_method(self):
        self.svc = PaymentService()

    @patch("src.services.payment_service.db_manager")
    def test_updates_payment_successfully(self, mock_db):
        mock_db.select.return_value = [make_payment_row()]
        mock_db.update.return_value = [make_payment_row(amount=750.00, status="pending")]
        from src.models import Payment as PaymentModel
        payment = PaymentModel(id="pay-001", member_id="mem-001", amount=750.00, status=PaymentStatus.PENDING)
        result = self.svc.update_payment(payment)
        assert result.success is True
        assert result.data.status == PaymentStatus.PENDING
        assert result.data.amount == 750.0

    @patch("src.services.payment_service.db_manager")
    def test_missing_id_returns_failure(self, mock_db):
        from src.models import Payment as PaymentModel
        payment = PaymentModel(member_id="mem-001", amount=500.00)
        result = self.svc.update_payment(payment)
        assert result.success is False
        assert "ID" in result.error
        mock_db.update.assert_not_called()

    @patch("src.services.payment_service.db_manager")
    def test_validation_error_blocks_update(self, mock_db):
        from src.models import Payment as PaymentModel
        payment = PaymentModel(id="pay-001", member_id="mem-001", amount=0.0)
        result = self.svc.update_payment(payment)
        assert result.success is False
        mock_db.update.assert_not_called()

    @patch("src.services.payment_service.db_manager")
    def test_payment_not_found_returns_failure(self, mock_db):
        mock_db.select.return_value = []
        from src.models import Payment as PaymentModel
        payment = PaymentModel(id="pay-999", member_id="mem-001", amount=500.00)
        result = self.svc.update_payment(payment)
        assert result.success is False
        assert "not found" in result.error.lower()

    @patch("src.services.payment_service.db_manager")
    def test_created_by_is_excluded_from_update_payload(self, mock_db):
        mock_db.select.return_value = [make_payment_row()]
        mock_db.update.return_value = [make_payment_row()]
        from src.models import Payment as PaymentModel
        payment = PaymentModel(id="pay-001", member_id="mem-001", amount=500.00, created_by="user-001")
        self.svc.update_payment(payment)
        payload = mock_db.update.call_args.args[1]
        assert 'created_by' not in payload

    @patch("src.services.payment_service.db_manager")
    def test_db_exception_returns_failure(self, mock_db):
        mock_db.select.return_value = [make_payment_row()]
        mock_db.update.side_effect = Exception("update failed")
        from src.models import Payment as PaymentModel
        payment = PaymentModel(id="pay-001", member_id="mem-001", amount=500.00)
        result = self.svc.update_payment(payment)
        assert result.success is False
