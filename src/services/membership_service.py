from __future__ import annotations
import logging
from typing import Optional
from datetime import date, datetime, timedelta
from src.database import db_manager
from src.models import Member, MemberMembership, MembershipPlan
from src.models.enums import MembershipStatus
from src.services import ServiceResult

_PLANS_TABLE = 'membership_plans'
_MEMBERSHIPS_TABLE = 'member_memberships'

_MEMBERSHIP_COLUMNS = (
    "member_memberships.id, member_memberships.member_id, "
    "member_memberships.membership_plan_id, member_memberships.start_date, "
    "member_memberships.end_date, member_memberships.status, "
    "member_memberships.auto_renew, member_memberships.notes, "
    "member_memberships.created_at, member_memberships.updated_at, "
    "member_memberships.created_by, "
    "members.member_code, members.first_name, members.last_name, "
    "membership_plans.name AS plan_name, membership_plans.duration_days, membership_plans.price"
)
_MEMBERSHIP_JOINS = [
    "LEFT JOIN members ON members.id = member_memberships.member_id",
    "LEFT JOIN membership_plans ON membership_plans.id = member_memberships.membership_plan_id",
]


class MembershipService:

    """Service layer for managing gym memberships, including business logic for creating, updating, and validating memberships."""

    def get_all_plans(self, include_inactive: bool = False) -> ServiceResult[list[MembershipPlan]]:
        """Fetches all membership plans, optionally including inactive ones."""
        try:

            filters = None if include_inactive else {'is_active': True}
            rows = db_manager.select(
                table=_PLANS_TABLE,
                filters=filters,
                order_by='name'
            )
            plans = [self._row_to_plan(row) for row in rows]
            return ServiceResult.ok(plans)

        except Exception as e:
            logging.error(f"Error fetching membership plans: {e}")
            return ServiceResult.fail(str(e))

    def get_plan_by_id(self, plan_id: str) -> ServiceResult[MembershipPlan]:

        try:
            rows = db_manager.select(table=_PLANS_TABLE, filters={'id': plan_id})
            if not rows:
                return ServiceResult.not_found("Membership plan not found")
            return ServiceResult.ok(self._row_to_plan(rows[0]))

        except Exception as e:
            logging.error(f"Error fetching membership plan by ID: {e}")
            return ServiceResult.fail(str(e))

    def create_plan(self, plan: MembershipPlan) -> ServiceResult[MembershipPlan]:
        """Validates and persists a new membership plan to the database."""
        validation_error = self._validate_plan(plan)
        if validation_error:
            return ServiceResult.fail(validation_error)

        try:
            row = db_manager.insert(_PLANS_TABLE, self._plan_to_row(plan))
            return ServiceResult.ok(self._row_to_plan(row))

        except Exception as e:
            logging.error(f"Error creating membership plan: {e}")
            return ServiceResult.fail(str(e))

    def update_plan(self, plan: MembershipPlan) -> ServiceResult[MembershipPlan]:
        """Updates an existing membership plan. Requires a valid plan.id."""
        if not plan.id:
            return ServiceResult.fail("Plan ID is required for updates")

        validation_error = self._validate_plan(plan)
        if validation_error:
            return ServiceResult.fail(validation_error)

        try:
            existing = self.get_plan_by_id(plan.id)
            if not existing.success:
                return ServiceResult.fail("Membership plan not found")

            data = self._plan_to_row(plan)
            data['updated_at'] = datetime.now().isoformat()

            rows = db_manager.update(_PLANS_TABLE, data, filters={'id': plan.id})
            return ServiceResult.ok(self._row_to_plan(rows[0]))

        except Exception as e:
            logging.error(f"Error updating membership plan {plan.id}: {e}")
            return ServiceResult.fail(str(e))

    def toggle_plan_status(self, plan_id: str, is_active: bool) -> ServiceResult[bool]:
        """Activates or deactivates a membership plan."""
        try:
            db_manager.update(
                _PLANS_TABLE,
                {'is_active': is_active},
                filters={'id': plan_id}
            )
            return ServiceResult.ok(True)

        except Exception as e:
            logging.error(f"Error toggling plan status for {plan_id}: {e}")
            return ServiceResult.fail(str(e))

    # ------------------------------------------------------------------ #
    # MemberMembership methods
    # ------------------------------------------------------------------ #

    def get_memberships(
        self,
        status: Optional[MembershipStatus] = None,
        search_term: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        expiring_days: Optional[int] = None,
    ) -> ServiceResult[list[MemberMembership]]:
        """Returns member memberships with optional filters.

        Filter priority:
        1. expiring_days — memberships expiring within N days (always active only)
        2. date_from / date_to — memberships whose start_date falls in the range
        3. status — equality filter on status column
        If search_term is given, results are filtered in Python by member name/code.
        """

        try:
            if expiring_days is not None:
                today = date.today()
                rows = db_manager.select_range(
                    table=_MEMBERSHIPS_TABLE,
                    column='end_date',
                    start=today.isoformat(),
                    end=(today + timedelta(days=expiring_days)).isoformat(),
                    columns=_MEMBERSHIP_COLUMNS,
                    joins=_MEMBERSHIP_JOINS,
                    filters={'status': MembershipStatus.ACTIVE.value},
                    order_by='end_date',
                )
            elif date_from and date_to:
                extra_filters = {'status': status.value} if status else None
                rows = db_manager.select_range(
                    table=_MEMBERSHIPS_TABLE,
                    column='start_date',
                    start=date_from.isoformat(),
                    end=date_to.isoformat(),
                    columns=_MEMBERSHIP_COLUMNS,
                    joins=_MEMBERSHIP_JOINS,
                    filters=extra_filters,
                    order_by='end_date',
                )
            else:
                filters = {'status': status.value} if status else None
                rows = db_manager.select(
                    table=_MEMBERSHIPS_TABLE,
                    columns=_MEMBERSHIP_COLUMNS,
                    joins=_MEMBERSHIP_JOINS,
                    filters=filters,
                    order_by='end_date',
                )

            memberships = [self._row_to_membership(row) for row in rows]

            if search_term:
                term = search_term.strip().lower()
                memberships = [
                    m for m in memberships
                    if m.member and (
                        term in m.member.full_name.lower() or
                        term in m.member.member_code.lower()
                    )
                ]

            return ServiceResult.ok(memberships)

        except Exception as e:
            logging.error(f"Error fetching memberships: {e}")
            return ServiceResult.fail(str(e))

    def get_memberships_by_member(self, member_id: str) -> ServiceResult[list[MemberMembership]]:
        """Returns all memberships for a specific member, ordered by start date."""

        try:
            rows = db_manager.select(
                table=_MEMBERSHIPS_TABLE,
                columns=_MEMBERSHIP_COLUMNS,
                joins=_MEMBERSHIP_JOINS,
                filters={'member_id': member_id},
                order_by='start_date',
            )
            memberships = [self._row_to_membership(row) for row in rows]
            return ServiceResult.ok(memberships)

        except Exception as e:
            logging.error(f"Error fetching memberships for member {member_id}: {e}")
            return ServiceResult.fail(str(e))

    def assign_membership(
        self,
        member_id: str,
        plan_id: str,
        start_date: date,
        notes: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> ServiceResult[MemberMembership]:
        """Assigns a membership plan to a member.

        Fails if the member already has an active membership.
        Calculates end_date automatically from the plan's duration_days.
        """
        try:
            # Validate no active membership exists
            existing = db_manager.select(
                table=_MEMBERSHIPS_TABLE,
                filters={'member_id': member_id, 'status': MembershipStatus.ACTIVE.value},
            )
            if existing:
                return ServiceResult.fail("This member already has an active membership")

            # Fetch plan to calculate end_date
            plan_result = self.get_plan_by_id(plan_id)
            if not plan_result.success:
                return ServiceResult.fail("The selected plan was not found")

            end_date = start_date + timedelta(days=plan_result.data.duration_days)

            data = {
                'member_id': member_id,
                'membership_plan_id': plan_id,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'status': MembershipStatus.ACTIVE.value,
                'notes': notes,
                'created_by': created_by,
            }

            row = db_manager.insert(_MEMBERSHIPS_TABLE, data)
            return ServiceResult.ok(self._row_to_membership(row))

        except Exception as e:
            logging.error(f"Error assigning membership to member {member_id}: {e}")
            return ServiceResult.fail(str(e))

    def change_status(
        self,
        membership_id: str,
        new_status: MembershipStatus,
    ) -> ServiceResult[bool]:
        """Changes the status of a membership. Only valid transitions are allowed.

        Allowed transitions:
        - ACTIVE    → SUSPENDED, CANCELLED
        - SUSPENDED → ACTIVE, CANCELLED
        - EXPIRED   → ACTIVE  (manual renewal)
        - CANCELLED → (none)
        """
        try:
            rows = db_manager.select(_MEMBERSHIPS_TABLE, filters={'id': membership_id})
            if not rows:
                return ServiceResult.not_found("Membership not found")

            current_status = MembershipStatus(rows[0]['status'])

            if not self._validate_status_transition(current_status, new_status):
                return ServiceResult.fail(
                    f"Cannot transition from '{current_status.value}' to '{new_status.value}'"
                )

            db_manager.update(
                _MEMBERSHIPS_TABLE,
                {'status': new_status.value},
                filters={'id': membership_id},
            )
            return ServiceResult.ok(True)

        except Exception as e:
            logging.error(f"Error changing status for membership {membership_id}: {e}")
            return ServiceResult.fail(str(e))

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _validate_plan(plan: MembershipPlan) -> Optional[str]:
        """Returns an error message if the plan is invalid, or None if valid."""
        if not plan.name or not plan.name.strip():
            return "Plan name is required"
        if plan.price < 0:
            return "Price must be zero or greater"
        if plan.duration_days < 1:
            return "Duration must be at least 1 day"
        return None

    @staticmethod
    def _plan_to_row(plan: MembershipPlan) -> dict:
        """Converts a MembershipPlan dataclass into a plain dict for the database."""
        return {
            'name': plan.name.strip(),
            'description': plan.description,
            'duration_days': plan.duration_days,
            'price': plan.price,
            'has_class_access': plan.has_class_access,
            'max_classes_per_week': plan.max_classes_per_week,
            'is_active': plan.is_active,
        }

    @staticmethod
    def _row_to_plan(row: dict) -> MembershipPlan:
        """Converts a raw database row into a MembershipPlan dataclass."""
        return MembershipPlan(
            id=row.get('id'),
            name=row.get('name', ''),
            description=row.get('description'),
            duration_days=row.get('duration_days', 30),
            price=float(row.get('price', 0.0)),
            has_class_access=row.get('has_class_access', True),
            max_classes_per_week=row.get('max_classes_per_week'),
            features=row.get('features'),
            is_active=row.get('is_active', True),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    @staticmethod
    def _row_to_membership(row: dict) -> MemberMembership:
        """Converts a raw database row (with joins) into a MemberMembership dataclass."""
        member_code = row.get('member_code')
        member = Member(
            id=row.get('member_id'),
            member_code=member_code or '',
            first_name=row.get('first_name', ''),
            last_name=row.get('last_name', ''),
        ) if member_code else None

        plan_name = row.get('plan_name')
        plan = MembershipPlan(
            id=row.get('membership_plan_id'),
            name=plan_name or '',
            duration_days=row.get('duration_days', 0),
            price=float(row.get('price', 0.0)),
        ) if plan_name else None

        def parse_date(value) -> Optional[date]:
            if not value:
                return None
            if isinstance(value, date):
                return value
            try:
                return date.fromisoformat(str(value))
            except ValueError:
                return None

        return MemberMembership(
            id=row.get('id'),
            member_id=row.get('member_id', ''),
            membership_plan_id=row.get('membership_plan_id', ''),
            start_date=parse_date(row.get('start_date')) or date.today(),
            end_date=parse_date(row.get('end_date')),
            status=MembershipStatus(row.get('status', MembershipStatus.ACTIVE.value)),
            auto_renew=row.get('auto_renew', False),
            notes=row.get('notes'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            created_by=row.get('created_by'),
            member=member,
            plan=plan,
        )

    @staticmethod
    def _validate_status_transition(current: MembershipStatus, new: MembershipStatus) -> bool:
        """Returns True if the transition from current to new status is allowed."""
        ALLOWED: dict[MembershipStatus, set[MembershipStatus]] = {
            MembershipStatus.ACTIVE:    {MembershipStatus.SUSPENDED, MembershipStatus.CANCELLED},
            MembershipStatus.SUSPENDED: {MembershipStatus.ACTIVE,    MembershipStatus.CANCELLED},
            MembershipStatus.EXPIRED:   {MembershipStatus.ACTIVE},
            MembershipStatus.CANCELLED: set(),
        }
        return new in ALLOWED.get(current, set())


# Global instance
membership_service = MembershipService()
