from __future__ import annotations
import logging
from typing import Optional
from datetime import datetime, date, timezone
from src.database import db_manager
from src.models import Payment, Member
from src.models.enums import PaymentMethod, PaymentStatus
from src.services import ServiceResult

_TABLE = 'payments'

_PAYMENT_COLUMNS = (
    "payments.id, payments.member_id, payments.membership_id, "
    "payments.amount, payments.payment_method, payments.payment_date, "
    "payments.status, payments.reference_number, payments.notes, "
    "payments.created_at, payments.created_by, "
    "members.member_code, members.first_name, members.last_name"
)
_PAYMENT_JOIN = ["LEFT JOIN members ON members.id = payments.member_id"]


class PaymentService:

    """Service layer for managing payments, including business logic for creating and updating payment records."""

    def get_payments(
        self,
        status: Optional[PaymentStatus] = None,
        payment_method: Optional[PaymentMethod] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search_term: Optional[str] = None,
    ) -> ServiceResult[list[Payment]]:
        """Returns payments with optional filters.

        If search_term is given, results are filtered in Python by member name/code.
        """
        try:
            filters = {}
            if status:
                filters['status'] = status.value
            if payment_method:
                filters['payment_method'] = payment_method.value

            if date_from and date_to:
                # payment_date is TIMESTAMPTZ — a bare date.isoformat() for date_to would mean
                # midnight, excluding same-day payments logged later that day. Expand the range
                # to the full local day before converting to UTC (same pattern as AttendanceService).
                local_tz = datetime.now().astimezone().tzinfo
                start = datetime.combine(date_from, datetime.min.time()).replace(tzinfo=local_tz).astimezone(timezone.utc).isoformat()
                end = datetime.combine(date_to, datetime.max.time()).replace(tzinfo=local_tz).astimezone(timezone.utc).isoformat()

                rows = db_manager.select_range(
                    table=_TABLE,
                    column='payment_date',
                    start=start,
                    end=end,
                    columns=_PAYMENT_COLUMNS,
                    joins=_PAYMENT_JOIN,
                    filters=filters if filters else None,
                    order_by='payment_date',
                )
            else:
                rows = db_manager.select(
                    table=_TABLE,
                    columns=_PAYMENT_COLUMNS,
                    joins=_PAYMENT_JOIN,
                    filters=filters if filters else None,
                    order_by='payment_date',
                )

            payments = [self._row_to_payment(row) for row in rows]

            if search_term:
                term = search_term.strip().lower()
                payments = [
                    p for p in payments
                    if p.member and (
                        term in p.member.full_name.lower() or
                        term in p.member.member_code.lower()
                    )
                ]

            return ServiceResult.ok(payments)

        except Exception as e:
            logging.error(f"Error fetching payments: {e}")
            return ServiceResult.fail(str(e))

    def get_payments_by_member(self, member_id: str) -> ServiceResult[list[Payment]]:
        """Returns all payments for a specific member, ordered by payment date."""
        try:
            rows = db_manager.select(
                table=_TABLE,
                columns=_PAYMENT_COLUMNS,
                joins=_PAYMENT_JOIN,
                filters={'member_id': member_id},
                order_by='payment_date',
            )
            payments = [self._row_to_payment(row) for row in rows]
            return ServiceResult.ok(payments)

        except Exception as e:
            logging.error(f"Error fetching payments for member {member_id}: {e}")
            return ServiceResult.fail(str(e))

    def create_payment(self, payment: Payment, created_by: Optional[str] = None) -> ServiceResult[Payment]:
        """Validates and persists a new payment record."""
        validation_error = self._validate_payment(payment)
        if validation_error:
            return ServiceResult.fail(validation_error)

        try:
            data = self._payment_to_row(payment)
            data['created_by'] = created_by

            row = db_manager.insert(_TABLE, data)
            return ServiceResult.ok(self._row_to_payment(row))

        except Exception as e:
            logging.error(f"Error creating payment: {e}")
            return ServiceResult.fail(str(e))

    def update_payment(self, payment: Payment) -> ServiceResult[Payment]:
        """Updates an existing payment record. Requires a valid payment.id."""
        if not payment.id:
            return ServiceResult.fail("Payment ID is required for updates")

        validation_error = self._validate_payment(payment)
        if validation_error:
            return ServiceResult.fail(validation_error)

        try:
            existing = db_manager.select(_TABLE, filters={'id': payment.id})
            if not existing:
                return ServiceResult.fail("Payment record not found")

            data = self._payment_to_row(payment)
            data.pop('created_by', None)

            rows = db_manager.update(_TABLE, data, filters={'id': payment.id})
            return ServiceResult.ok(self._row_to_payment(rows[0]))

        except Exception as e:
            logging.error(f"Error updating payment {payment.id}: {e}")
            return ServiceResult.fail(str(e))

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _validate_payment(payment: Payment) -> Optional[str]:
        """Returns an error message if the payment is invalid, or None if valid."""
        if not payment.member_id:
            return "Member is required"
        if payment.amount <= 0:
            return "Amount must be greater than zero"
        return None

    @staticmethod
    def _payment_to_row(payment: Payment) -> dict:
        """Converts a Payment dataclass into a plain dict for the database."""
        return {
            'member_id': payment.member_id,
            'membership_id': payment.membership_id,
            'amount': payment.amount,
            'payment_method': payment.payment_method.value,
            'payment_date': payment.payment_date.isoformat(),
            'status': payment.status.value,
            'reference_number': payment.reference_number,
            'notes': payment.notes,
        }

    @staticmethod
    def _row_to_payment(row: dict) -> Payment:
        """Converts a raw database row (with joins) into a Payment dataclass."""
        member_code = row.get('member_code')
        member = Member(
            id=row.get('member_id'),
            member_code=member_code or '',
            first_name=row.get('first_name', ''),
            last_name=row.get('last_name', ''),
        ) if member_code else None

        def parse_dt(value) -> Optional[datetime]:
            if not value:
                return None
            if isinstance(value, datetime):
                return value
            try:
                return datetime.fromisoformat(str(value))
            except ValueError:
                return None

        return Payment(
            id=row.get('id'),
            member_id=row.get('member_id', ''),
            membership_id=row.get('membership_id'),
            amount=float(row.get('amount', 0.0)),
            payment_method=PaymentMethod(row.get('payment_method', PaymentMethod.CASH.value)),
            payment_date=parse_dt(row.get('payment_date')) or datetime.now(),
            status=PaymentStatus(row.get('status', PaymentStatus.COMPLETED.value)),
            reference_number=row.get('reference_number'),
            notes=row.get('notes'),
            created_at=row.get('created_at'),
            created_by=row.get('created_by'),
            member=member,
        )


# Global instance
payment_service = PaymentService()
