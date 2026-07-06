from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

from src.database import db_manager
from src.models import Equipment, EquipmentMaintenance
from src.models.enums import EquipmentCondition, MaintenanceType
from src.services import ServiceResult

logger = logging.getLogger(__name__)

_EQUIPMENT_TABLE = 'equipment'
_MAINTENANCE_TABLE = 'equipment_maintenance'

_SEARCHABLE_COLUMNS = ('name', 'category', 'brand')

_MAINTENANCE_COLUMNS = (
    "equipment_maintenance.id, equipment_maintenance.equipment_id, "
    "equipment_maintenance.maintenance_date, equipment_maintenance.maintenance_type, "
    "equipment_maintenance.description, equipment_maintenance.cost, "
    "equipment_maintenance.performed_by, equipment_maintenance.next_maintenance_date, "
    "equipment_maintenance.created_at, equipment_maintenance.created_by, "
    "equipment.name AS equipment_name"
)
_MAINTENANCE_JOINS = [
    "LEFT JOIN equipment ON equipment.id = equipment_maintenance.equipment_id",
]


class EquipmentService:
    """Service layer for managing gym equipment and its maintenance history."""

    # ------------------------------------------------------------------ #
    # Equipment methods
    # ------------------------------------------------------------------ #

    def get_all_equipment(self, include_inactive: bool = False) -> ServiceResult[list[Equipment]]:
        """Fetches all equipment items, optionally including inactive ones."""
        try:
            filters = None if include_inactive else {'is_active': True}
            rows = db_manager.select(
                table=_EQUIPMENT_TABLE,
                filters=filters,
                order_by='name',
            )
            equipment = [self._row_to_equipment(row) for row in rows]
            return ServiceResult.ok(equipment)

        except Exception as e:
            logger.error(f"Failed to fetch equipment: {e}")
            return ServiceResult.fail(f"Could not retrieve equipment: {e}")

    def get_equipment_by_id(self, equipment_id: str) -> ServiceResult[Equipment]:
        """Retrieves a single equipment item by its primary key."""
        try:
            rows = db_manager.select(table=_EQUIPMENT_TABLE, filters={'id': equipment_id})
            if not rows:
                return ServiceResult.not_found(f"Equipment with id '{equipment_id}' not found")
            return ServiceResult.ok(self._row_to_equipment(rows[0]))

        except Exception as e:
            logger.error(f"Failed to fetch equipment {equipment_id}: {e}")
            return ServiceResult.fail(f"Could not retrieve equipment: {e}")

    def search_equipment(self, term: str, column: Optional[str] = None) -> ServiceResult[list[Equipment]]:
        """
        Searches for active equipment by a partial, case-insensitive match.

        Args:
            term:   The search string.
            column: When provided, restricts the search to that single column
                    ('name', 'category', or 'brand'). When None, searches
                    across all three columns and merges unique results.
        """
        if not term or not term.strip():
            return ServiceResult.fail("Search term cannot be empty")

        if column and column in _SEARCHABLE_COLUMNS:
            columns_to_search = (column,)
        else:
            columns_to_search = _SEARCHABLE_COLUMNS

        try:
            seen_ids: set[str] = set()
            equipment: list[Equipment] = []

            for col in columns_to_search:
                rows = db_manager.search(
                    table=_EQUIPMENT_TABLE,
                    column=col,
                    search_term=term.strip(),
                    filters={'is_active': True},
                )
                for row in rows:
                    if row['id'] not in seen_ids:
                        seen_ids.add(row['id'])
                        equipment.append(self._row_to_equipment(row))

            return ServiceResult.ok(equipment)

        except Exception as e:
            logger.error(f"Equipment search failed for term '{term}': {e}")
            return ServiceResult.fail(f"Search failed: {e}")

    def create_equipment(self, equipment: Equipment) -> ServiceResult[Equipment]:
        """Validates and persists a new equipment item to the database."""
        validation_error = self._validate_equipment(equipment)
        if validation_error:
            return ServiceResult.fail(validation_error)

        try:
            data = self._equipment_to_row(equipment)
            data['created_at'] = datetime.now().isoformat()
            data['updated_at'] = datetime.now().isoformat()

            row = db_manager.insert(table=_EQUIPMENT_TABLE, data=data)
            created = self._row_to_equipment(row)

            logger.info(f"Equipment created: {created.id} — {created.name}")
            return ServiceResult.ok(created)

        except Exception as e:
            logger.error(f"Failed to create equipment: {e}")
            return ServiceResult.fail(f"Could not create equipment: {e}")

    def update_equipment(self, equipment: Equipment) -> ServiceResult[Equipment]:
        """Updates an existing equipment item. Requires a valid equipment.id."""
        if not equipment.id:
            return ServiceResult.fail("Equipment id is required for updates")

        validation_error = self._validate_equipment(equipment)
        if validation_error:
            return ServiceResult.fail(validation_error)

        try:
            existing = db_manager.select(table=_EQUIPMENT_TABLE, filters={'id': equipment.id})
            if not existing:
                return ServiceResult.fail(f"Equipment with id '{equipment.id}' not found")

            data = self._equipment_to_row(equipment)
            data['updated_at'] = datetime.now().isoformat()
            data.pop('created_at', None)  # Never overwrite creation timestamp

            rows = db_manager.update(table=_EQUIPMENT_TABLE, data=data, filters={'id': equipment.id})
            updated = self._row_to_equipment(rows[0])

            logger.info(f"Equipment updated: {equipment.id} — {equipment.name}")
            return ServiceResult.ok(updated)

        except Exception as e:
            logger.error(f"Failed to update equipment {equipment.id}: {e}")
            return ServiceResult.fail(f"Could not update equipment: {e}")

    # ------------------------------------------------------------------ #
    # Maintenance methods
    # ------------------------------------------------------------------ #

    def get_maintenance_records(
        self,
        equipment_id: Optional[str] = None,
        maintenance_type: Optional[MaintenanceType] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> ServiceResult[list[EquipmentMaintenance]]:
        """Returns maintenance records with optional filters, most recent first."""
        try:
            filters = {}
            if equipment_id:
                filters['equipment_id'] = equipment_id
            if maintenance_type:
                filters['maintenance_type'] = maintenance_type.value

            if date_from and date_to:
                rows = db_manager.select_range(
                    table=_MAINTENANCE_TABLE,
                    column='maintenance_date',
                    start=date_from.isoformat(),
                    end=date_to.isoformat(),
                    columns=_MAINTENANCE_COLUMNS,
                    joins=_MAINTENANCE_JOINS,
                    filters=filters or None,
                    order_by='maintenance_date',
                )
            else:
                rows = db_manager.select(
                    table=_MAINTENANCE_TABLE,
                    columns=_MAINTENANCE_COLUMNS,
                    joins=_MAINTENANCE_JOINS,
                    filters=filters or None,
                    order_by='maintenance_date',
                )

            records = [self._row_to_maintenance(row) for row in rows]
            return ServiceResult.ok(records)

        except Exception as e:
            logger.error(f"Failed to fetch maintenance records: {e}")
            return ServiceResult.fail(f"Could not retrieve maintenance records: {e}")

    def get_maintenance_by_equipment(self, equipment_id: str) -> ServiceResult[list[EquipmentMaintenance]]:
        """Returns all maintenance records for a specific equipment item."""
        try:
            rows = db_manager.select(
                table=_MAINTENANCE_TABLE,
                columns=_MAINTENANCE_COLUMNS,
                joins=_MAINTENANCE_JOINS,
                filters={'equipment_id': equipment_id},
                order_by='maintenance_date',
            )
            records = [self._row_to_maintenance(row) for row in rows]
            return ServiceResult.ok(records)

        except Exception as e:
            logger.error(f"Failed to fetch maintenance for equipment {equipment_id}: {e}")
            return ServiceResult.fail(f"Could not retrieve maintenance records: {e}")

    def log_maintenance(
        self,
        equipment_id: str,
        maintenance_date: date,
        maintenance_type: MaintenanceType,
        description: Optional[str] = None,
        cost: Optional[float] = None,
        performed_by: Optional[str] = None,
        next_maintenance_date: Optional[date] = None,
        created_by: Optional[str] = None,
    ) -> ServiceResult[EquipmentMaintenance]:
        """Logs a maintenance event performed on a piece of equipment."""
        if not equipment_id:
            return ServiceResult.fail("Equipment is required")

        if not maintenance_date:
            return ServiceResult.fail("Maintenance date is required")

        try:
            equipment_result = self.get_equipment_by_id(equipment_id)
            if not equipment_result.success:
                return ServiceResult.fail("The selected equipment was not found")

            data = {
                'equipment_id': equipment_id,
                'maintenance_date': maintenance_date.isoformat(),
                'maintenance_type': maintenance_type.value,
                'description': description,
                'cost': cost,
                'performed_by': performed_by,
                'next_maintenance_date': next_maintenance_date.isoformat() if next_maintenance_date else None,
                'created_by': created_by,
            }

            row = db_manager.insert(table=_MAINTENANCE_TABLE, data=data)
            row['equipment_name'] = equipment_result.data.name  # insert() has no join, add it back
            created = self._row_to_maintenance(row)

            logger.info(f"Maintenance logged: {created.id} for equipment {equipment_id}")
            return ServiceResult.ok(created)

        except Exception as e:
            logger.error(f"Failed to log maintenance for equipment {equipment_id}: {e}")
            return ServiceResult.fail(f"Could not log maintenance: {e}")

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _validate_equipment(equipment: Equipment) -> Optional[str]:
        """Returns an error message if the equipment is invalid, or None if valid."""
        if not equipment.name or not equipment.name.strip():
            return "Equipment name is required"
        if equipment.purchase_price is not None and equipment.purchase_price < 0:
            return "Purchase price must be zero or greater"
        return None

    @staticmethod
    def _equipment_to_row(equipment: Equipment) -> dict:
        """Converts an Equipment dataclass into a plain dict suitable for the database."""
        return {
            'name': equipment.name.strip(),
            'category': equipment.category,
            'brand': equipment.brand,
            'model': equipment.model,
            'serial_number': equipment.serial_number,
            'purchase_date': equipment.purchase_date.isoformat() if equipment.purchase_date else None,
            'purchase_price': equipment.purchase_price,
            'condition': equipment.condition.value,
            'location': equipment.location,
            'notes': equipment.notes,
            'is_active': equipment.is_active,
        }

    @staticmethod
    def _row_to_equipment(row: dict) -> Equipment:
        """Converts a raw database row into an Equipment dataclass."""

        def parse_date(value) -> Optional[date]:
            if not value:
                return None
            if isinstance(value, date):
                return value
            try:
                return date.fromisoformat(str(value))
            except ValueError:
                return None

        return Equipment(
            id=row.get('id'),
            name=row.get('name', ''),
            category=row.get('category'),
            brand=row.get('brand'),
            model=row.get('model'),
            serial_number=row.get('serial_number'),
            purchase_date=parse_date(row.get('purchase_date')),
            purchase_price=float(row['purchase_price']) if row.get('purchase_price') is not None else None,
            condition=EquipmentCondition(row['condition']) if row.get('condition') else EquipmentCondition.GOOD,
            location=row.get('location'),
            notes=row.get('notes'),
            is_active=row.get('is_active', True),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )

    @staticmethod
    def _row_to_maintenance(row: dict) -> EquipmentMaintenance:
        """Converts a raw database row (with joined equipment name) into an EquipmentMaintenance dataclass."""

        def parse_date(value) -> Optional[date]:
            if not value:
                return None
            if isinstance(value, date):
                return value
            try:
                return date.fromisoformat(str(value))
            except ValueError:
                return None

        equipment_name = row.get('equipment_name')
        equipment = Equipment(id=row.get('equipment_id'), name=equipment_name) if equipment_name else None

        return EquipmentMaintenance(
            id=row.get('id'),
            equipment_id=row.get('equipment_id', ''),
            maintenance_date=parse_date(row.get('maintenance_date')) or date.today(),
            maintenance_type=MaintenanceType(row.get('maintenance_type', MaintenanceType.PREVENTIVE.value)),
            description=row.get('description'),
            cost=float(row['cost']) if row.get('cost') is not None else None,
            performed_by=row.get('performed_by'),
            next_maintenance_date=parse_date(row.get('next_maintenance_date')),
            created_at=row.get('created_at'),
            created_by=row.get('created_by'),
            equipment=equipment,
        )


# Global instance
equipment_service = EquipmentService()
