from datetime import datetime, date, timezone
from typing import Optional
from src.database import db_manager
from src.models import Attendance, Member
from src.services import ServiceResult

_TABLE = 'attendance'
_MEMBERS_TABLE = 'members'

class AttendanceService:

    # Public methods
    def get_attendance_by_date(self, filter_date: date) -> ServiceResult[list[Attendance]]:
        """Returns all attendance records for a given date, with member info."""

        try:
            start = datetime.combine(filter_date, datetime.min.time()).isoformat()
            end = datetime.combine(filter_date, datetime.max.time()).isoformat()

            rows = db_manager.select(
                table=_TABLE,
                columns="*, members(member_code, first_name, last_name)",
                order_by="check_in_time",
            )

            attendance_records = []
            for row in rows:
                ci = row.get('check_in_time', "")
                if start <= ci <= end:
                    attendance_records.append(self._row_to_attendance(row))
            
            return ServiceResult.ok(attendance_records)
        except Exception as e:
            return ServiceResult.fail(str(e))

    def search_member_for_checkin(self, term: str) -> ServiceResult[list[Member]]:
        """Searches active members by member_code or full name (ILIKE)."""

        try:
            # Search by member_code
            rows_by_code = db_manager.search(
                table=_MEMBERS_TABLE,
                column="member_code",
                search_term = term,
                filters={"is_active": True}
            )

            # Search by first_name
            rows_by_name = db_manager.search(
                table=_MEMBERS_TABLE,
                column="first_name || ' ' || last_name",
                search_term = term,
                filters={"is_active": True}
            )

            seen = set()
            members = []

            for row in rows_by_code + rows_by_name:
                if row['id'] not in seen:
                    seen.add(row['id'])
                    members.append(self._row_to_member(row))

            if not members:
                return ServiceResult.not_found("No active member found with that code or name")
            
            return ServiceResult.ok(members)
        except Exception as e:
            return ServiceResult.fail(str(e))
        
    def check_in(self, member_id: str, created_by: Optional[str] = None) -> ServiceResult[Attendance]:
        """Creates a check-in record. Fails if the member already has an open check-in today."""

        try:
            validation_error = self._validate_no_open_checkin(member_id)
            if validation_error:
                return ServiceResult.fail(validation_error)
            
            now = datetime.now(timezone.utc).isoformat()
            data =  {
                "member_id": member_id,
                "check_in_time": now,
                "created_by": created_by
            }

            row = db_manager.insert(_TABLE, data)
            return ServiceResult.ok(self._row_to_attendance(row))
        except Exception as e:
            return ServiceResult.fail(str(e))
    
    def check_out(self, attendance_id: str) -> ServiceResult[Attendance]:
        """Sets check_out_time on an existing open attendance record."""

        try:
            now = datetime.now(timezone.utc).isoformat()
            rows = db_manager.update(
                table=_TABLE,
                data={"check_out_time": now},
                filters={"id": attendance_id},
            )

            if not rows:
                return ServiceResult.fail("Attendance record not found")
            return ServiceResult.ok(self._row_to_attendance(rows[0]))
        except Exception as e:
            return ServiceResult.fail(str(e))

    # Private helper methods
    def _validate_no_open_checkin(self, member_id: str) -> Optional[str]:
        """Returns an error string if the member already has an open check-in today."""

        today = date.today()
        start = datetime.combine(today, datetime.min.time()).isoformat()
        end = datetime.combine(today, datetime.max.time()).isoformat()

        rows = db_manager.select(
            table=_TABLE,
            filters = {"member_id": member_id}
        )

        for row in rows:
            ci = row.get('check_in_time', "")
            if start <= ci <= end and row.get('check_out_time') is None:
                return "This member already has an open check-in today"
    
    @staticmethod
    def _row_to_attendance(row: dict) -> Attendance:
        member_data = row.get("members")
        member = None
        if member_data:
            member = Member(
                id=row.get("member_id"),
                member_code=member_data.get("member_code", ""),
                first_name=member_data.get("first_name", ""),
                last_name=member_data.get("last_name", ""),
            )
        def parse_dt(value) -> Optional[datetime]:
            if not value:
                return None
            if isinstance(value, datetime):
                return value
            try:
                return datetime.fromisoformat(str(value))
            except ValueError:
                return None
        return Attendance(
            id=row.get("id"),
            member_id=row.get("member_id", ""),
            check_in_time=parse_dt(row.get("check_in_time")) or datetime.now(),
            check_out_time=parse_dt(row.get("check_out_time")),
            notes=row.get("notes"),
            created_by=row.get("created_by"),
            member=member,
        )
    @staticmethod
    def _row_to_member(row: dict) -> Member:
        return Member(
            id=row.get("id"),
            member_code=row.get("member_code", ""),
            first_name=row.get("first_name", ""),
            last_name=row.get("last_name", ""),
            is_active=row.get("is_active", True),
        )
    
attendance_service = AttendanceService()