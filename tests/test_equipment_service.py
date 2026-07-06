"""
Tests for EquipmentService.

All database interactions are isolated by patching the global `db_manager`
singleton that `equipment_service` imports at module level.

Patch target: 'src.services.equipment_service.db_manager'
"""
from unittest.mock import patch
from datetime import date

from src.services.equipment_service import EquipmentService
from src.models.models import Equipment, EquipmentMaintenance
from src.models.enums import EquipmentCondition, MaintenanceType


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

def make_equipment(**kwargs) -> Equipment:
    """Factory for a valid Equipment with sensible defaults."""
    defaults = dict(
        id="uuid-001",
        name="Treadmill",
        category="Cardio",
        brand="Technogym",
        model="Run Personal",
        serial_number="SN-12345",
        purchase_date=date(2022, 3, 1),
        purchase_price=4500.00,
        condition=EquipmentCondition.GOOD,
        location="Main Floor",
        is_active=True,
    )
    defaults.update(kwargs)
    return Equipment(**defaults)


def make_equipment_row(**kwargs) -> dict:
    """Factory for a raw DB row matching the equipment table schema."""
    defaults = dict(
        id="uuid-001",
        name="Treadmill",
        category="Cardio",
        brand="Technogym",
        model="Run Personal",
        serial_number="SN-12345",
        purchase_date=date(2022, 3, 1),
        purchase_price=4500.00,
        condition="good",
        location="Main Floor",
        notes=None,
        is_active=True,
        created_at=None,
        updated_at=None,
    )
    defaults.update(kwargs)
    return defaults


def make_maintenance_row(**kwargs) -> dict:
    """Factory for a raw DB row matching a joined equipment_maintenance query."""
    defaults = dict(
        id="maint-001",
        equipment_id="uuid-001",
        maintenance_date=date(2024, 6, 1),
        maintenance_type="preventive",
        description="Belt lubrication",
        cost=50.0,
        performed_by="Acme Service Co.",
        next_maintenance_date=date(2024, 12, 1),
        created_at=None,
        created_by=None,
        equipment_name="Treadmill",
    )
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# _validate_equipment  (pure static)
# ---------------------------------------------------------------------------

class TestValidateEquipment:
    def setup_method(self):
        self.svc = EquipmentService()

    def test_valid_equipment_returns_none(self):
        assert self.svc._validate_equipment(make_equipment()) is None

    def test_missing_name_returns_error(self):
        e = make_equipment(name="")
        assert self.svc._validate_equipment(e) == "Equipment name is required"

    def test_whitespace_only_name_returns_error(self):
        e = make_equipment(name="   ")
        assert self.svc._validate_equipment(e) == "Equipment name is required"

    def test_negative_price_returns_error(self):
        e = make_equipment(purchase_price=-10.0)
        assert self.svc._validate_equipment(e) == "Purchase price must be zero or greater"

    def test_zero_price_is_valid(self):
        e = make_equipment(purchase_price=0.0)
        assert self.svc._validate_equipment(e) is None

    def test_none_price_is_valid(self):
        e = make_equipment(purchase_price=None)
        assert self.svc._validate_equipment(e) is None


# ---------------------------------------------------------------------------
# _equipment_to_row / _row_to_equipment  (pure static)
# ---------------------------------------------------------------------------

class TestEquipmentToRow:
    def test_basic_fields_are_present(self):
        e = make_equipment()
        row = EquipmentService._equipment_to_row(e)
        assert row["name"] == "Treadmill"
        assert row["category"] == "Cardio"
        assert row["condition"] == "good"

    def test_name_is_stripped(self):
        e = make_equipment(name="  Treadmill  ")
        row = EquipmentService._equipment_to_row(e)
        assert row["name"] == "Treadmill"

    def test_purchase_date_is_isoformatted(self):
        e = make_equipment(purchase_date=date(2021, 5, 20))
        row = EquipmentService._equipment_to_row(e)
        assert row["purchase_date"] == "2021-05-20"

    def test_null_purchase_date_stays_none(self):
        e = make_equipment(purchase_date=None)
        row = EquipmentService._equipment_to_row(e)
        assert row["purchase_date"] is None

    def test_condition_enum_is_converted_to_string(self):
        e = make_equipment(condition=EquipmentCondition.OUT_OF_SERVICE)
        row = EquipmentService._equipment_to_row(e)
        assert row["condition"] == "out_of_service"


class TestRowToEquipment:
    def test_basic_fields_are_mapped(self):
        row = make_equipment_row()
        e = EquipmentService._row_to_equipment(row)
        assert e.id == "uuid-001"
        assert e.name == "Treadmill"
        assert e.category == "Cardio"

    def test_condition_string_is_converted_to_enum(self):
        row = make_equipment_row(condition="fair")
        e = EquipmentService._row_to_equipment(row)
        assert e.condition == EquipmentCondition.FAIR

    def test_missing_condition_defaults_to_good(self):
        row = make_equipment_row()
        row.pop("condition")
        e = EquipmentService._row_to_equipment(row)
        assert e.condition == EquipmentCondition.GOOD

    def test_purchase_price_is_float(self):
        row = make_equipment_row(purchase_price="4500.00")
        e = EquipmentService._row_to_equipment(row)
        assert e.purchase_price == 4500.00

    def test_null_purchase_price_stays_none(self):
        row = make_equipment_row(purchase_price=None)
        e = EquipmentService._row_to_equipment(row)
        assert e.purchase_price is None

    def test_is_active_defaults_to_true_when_missing(self):
        row = make_equipment_row()
        row.pop("is_active")
        e = EquipmentService._row_to_equipment(row)
        assert e.is_active is True


# ---------------------------------------------------------------------------
# _row_to_maintenance  (pure static)
# ---------------------------------------------------------------------------

class TestRowToMaintenance:
    def test_basic_fields_are_mapped(self):
        row = make_maintenance_row()
        m = EquipmentService._row_to_maintenance(row)
        assert m.id == "maint-001"
        assert m.equipment_id == "uuid-001"
        assert m.description == "Belt lubrication"

    def test_maintenance_type_is_converted_to_enum(self):
        row = make_maintenance_row(maintenance_type="corrective")
        m = EquipmentService._row_to_maintenance(row)
        assert m.maintenance_type == MaintenanceType.CORRECTIVE

    def test_equipment_is_populated_when_name_present(self):
        row = make_maintenance_row()
        m = EquipmentService._row_to_maintenance(row)
        assert m.equipment is not None
        assert m.equipment.name == "Treadmill"

    def test_equipment_is_none_when_name_missing(self):
        row = make_maintenance_row(equipment_name=None)
        m = EquipmentService._row_to_maintenance(row)
        assert m.equipment is None

    def test_cost_is_float(self):
        row = make_maintenance_row(cost="50.0")
        m = EquipmentService._row_to_maintenance(row)
        assert m.cost == 50.0

    def test_null_cost_stays_none(self):
        row = make_maintenance_row(cost=None)
        m = EquipmentService._row_to_maintenance(row)
        assert m.cost is None

    def test_null_next_maintenance_date_stays_none(self):
        row = make_maintenance_row(next_maintenance_date=None)
        m = EquipmentService._row_to_maintenance(row)
        assert m.next_maintenance_date is None


# ---------------------------------------------------------------------------
# get_all_equipment
# ---------------------------------------------------------------------------

class TestGetAllEquipment:
    def setup_method(self):
        self.svc = EquipmentService()

    @patch("src.services.equipment_service.db_manager")
    def test_returns_list_on_success(self, mock_db):
        mock_db.select.return_value = [make_equipment_row(), make_equipment_row(id="uuid-002", name="Bench")]
        result = self.svc.get_all_equipment()
        assert result.success is True
        assert len(result.data) == 2

    @patch("src.services.equipment_service.db_manager")
    def test_active_only_passes_is_active_filter(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_all_equipment(include_inactive=False)
        mock_db.select.assert_called_once_with(
            table="equipment",
            filters={"is_active": True},
            order_by="name",
        )

    @patch("src.services.equipment_service.db_manager")
    def test_include_inactive_passes_no_filter(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_all_equipment(include_inactive=True)
        mock_db.select.assert_called_once_with(
            table="equipment",
            filters=None,
            order_by="name",
        )

    @patch("src.services.equipment_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.select.side_effect = Exception("connection lost")
        result = self.svc.get_all_equipment()
        assert result.success is False
        assert "Could not retrieve equipment" in result.error


# ---------------------------------------------------------------------------
# get_equipment_by_id
# ---------------------------------------------------------------------------

class TestGetEquipmentById:
    def setup_method(self):
        self.svc = EquipmentService()

    @patch("src.services.equipment_service.db_manager")
    def test_returns_equipment_when_found(self, mock_db):
        mock_db.select.return_value = [make_equipment_row()]
        result = self.svc.get_equipment_by_id("uuid-001")
        assert result.success is True
        assert result.data.id == "uuid-001"

    @patch("src.services.equipment_service.db_manager")
    def test_returns_not_found_when_missing(self, mock_db):
        mock_db.select.return_value = []
        result = self.svc.get_equipment_by_id("nonexistent")
        assert result.success is False
        assert result.is_not_found is True

    @patch("src.services.equipment_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.select.side_effect = Exception("timeout")
        result = self.svc.get_equipment_by_id("uuid-001")
        assert result.success is False


# ---------------------------------------------------------------------------
# search_equipment
# ---------------------------------------------------------------------------

class TestSearchEquipment:
    def setup_method(self):
        self.svc = EquipmentService()

    def test_empty_term_returns_fail(self):
        result = self.svc.search_equipment("")
        assert result.success is False
        assert "empty" in result.error.lower()

    @patch("src.services.equipment_service.db_manager")
    def test_searches_all_three_columns_by_default(self, mock_db):
        mock_db.search.return_value = []
        self.svc.search_equipment("tread")
        assert mock_db.search.call_count == 3
        called_columns = {c.kwargs["column"] for c in mock_db.search.call_args_list}
        assert called_columns == {"name", "category", "brand"}

    @patch("src.services.equipment_service.db_manager")
    def test_single_column_search_calls_db_once(self, mock_db):
        mock_db.search.return_value = []
        self.svc.search_equipment("tread", column="name")
        assert mock_db.search.call_count == 1
        mock_db.search.assert_called_once_with(
            table="equipment",
            column="name",
            search_term="tread",
            filters={"is_active": True},
        )

    @patch("src.services.equipment_service.db_manager")
    def test_deduplicates_results_across_columns(self, mock_db):
        row = make_equipment_row()
        mock_db.search.return_value = [row]
        result = self.svc.search_equipment("tread")
        assert result.success is True
        assert len(result.data) == 1

    @patch("src.services.equipment_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.search.side_effect = Exception("db error")
        result = self.svc.search_equipment("tread")
        assert result.success is False
        assert "Search failed" in result.error


# ---------------------------------------------------------------------------
# create_equipment
# ---------------------------------------------------------------------------

class TestCreateEquipment:
    def setup_method(self):
        self.svc = EquipmentService()

    @patch("src.services.equipment_service.db_manager")
    def test_creates_equipment_successfully(self, mock_db):
        mock_db.insert.return_value = make_equipment_row()
        result = self.svc.create_equipment(make_equipment(id=None))
        assert result.success is True
        assert result.data is not None

    @patch("src.services.equipment_service.db_manager")
    def test_validation_error_blocks_db_call(self, mock_db):
        result = self.svc.create_equipment(make_equipment(name=""))
        mock_db.insert.assert_not_called()
        assert result.success is False

    @patch("src.services.equipment_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.insert.side_effect = Exception("insert failed")
        result = self.svc.create_equipment(make_equipment())
        assert result.success is False
        assert "Could not create equipment" in result.error


# ---------------------------------------------------------------------------
# update_equipment
# ---------------------------------------------------------------------------

class TestUpdateEquipment:
    def setup_method(self):
        self.svc = EquipmentService()

    @patch("src.services.equipment_service.db_manager")
    def test_updates_equipment_successfully(self, mock_db):
        mock_db.select.return_value = [make_equipment_row()]
        mock_db.update.return_value = [make_equipment_row(name="Updated Treadmill")]
        result = self.svc.update_equipment(make_equipment())
        assert result.success is True
        assert result.data.name == "Updated Treadmill"

    def test_missing_id_returns_fail(self):
        result = self.svc.update_equipment(make_equipment(id=None))
        assert result.success is False
        assert "id is required" in result.error

    @patch("src.services.equipment_service.db_manager")
    def test_validation_error_blocks_db_call(self, mock_db):
        result = self.svc.update_equipment(make_equipment(name=""))
        mock_db.update.assert_not_called()
        assert result.success is False

    @patch("src.services.equipment_service.db_manager")
    def test_equipment_not_in_db_returns_fail(self, mock_db):
        mock_db.select.return_value = []
        result = self.svc.update_equipment(make_equipment())
        assert result.success is False
        assert "not found" in result.error

    @patch("src.services.equipment_service.db_manager")
    def test_immutable_fields_are_stripped_from_update_payload(self, mock_db):
        mock_db.select.return_value = [make_equipment_row()]
        mock_db.update.return_value = [make_equipment_row()]
        self.svc.update_equipment(make_equipment())
        update_data = mock_db.update.call_args.kwargs["data"]
        assert "created_at" not in update_data

    @patch("src.services.equipment_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.select.return_value = [make_equipment_row()]
        mock_db.update.side_effect = Exception("update failed")
        result = self.svc.update_equipment(make_equipment())
        assert result.success is False
        assert "Could not update equipment" in result.error


# ---------------------------------------------------------------------------
# get_maintenance_records
# ---------------------------------------------------------------------------

class TestGetMaintenanceRecords:
    def setup_method(self):
        self.svc = EquipmentService()

    @patch("src.services.equipment_service.db_manager")
    def test_returns_list_on_success(self, mock_db):
        mock_db.select.return_value = [make_maintenance_row()]
        result = self.svc.get_maintenance_records()
        assert result.success is True
        assert len(result.data) == 1

    @patch("src.services.equipment_service.db_manager")
    def test_uses_select_range_when_date_range_given(self, mock_db):
        mock_db.select_range.return_value = []
        self.svc.get_maintenance_records(date_from=date(2024, 1, 1), date_to=date(2024, 12, 31))
        mock_db.select_range.assert_called_once()
        mock_db.select.assert_not_called()

    @patch("src.services.equipment_service.db_manager")
    def test_filters_by_equipment_id(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_maintenance_records(equipment_id="uuid-001")
        mock_db.select.assert_called_once_with(
            table="equipment_maintenance",
            columns=mock_db.select.call_args.kwargs["columns"],
            joins=mock_db.select.call_args.kwargs["joins"],
            filters={"equipment_id": "uuid-001"},
            order_by="maintenance_date",
        )

    @patch("src.services.equipment_service.db_manager")
    def test_filters_by_maintenance_type(self, mock_db):
        mock_db.select.return_value = []
        self.svc.get_maintenance_records(maintenance_type=MaintenanceType.CORRECTIVE)
        assert mock_db.select.call_args.kwargs["filters"] == {"maintenance_type": "corrective"}

    @patch("src.services.equipment_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.select.side_effect = Exception("db error")
        result = self.svc.get_maintenance_records()
        assert result.success is False


# ---------------------------------------------------------------------------
# get_maintenance_by_equipment
# ---------------------------------------------------------------------------

class TestGetMaintenanceByEquipment:
    def setup_method(self):
        self.svc = EquipmentService()

    @patch("src.services.equipment_service.db_manager")
    def test_returns_records_for_equipment(self, mock_db):
        mock_db.select.return_value = [make_maintenance_row()]
        result = self.svc.get_maintenance_by_equipment("uuid-001")
        assert result.success is True
        assert len(result.data) == 1

    @patch("src.services.equipment_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.select.side_effect = Exception("db error")
        result = self.svc.get_maintenance_by_equipment("uuid-001")
        assert result.success is False


# ---------------------------------------------------------------------------
# log_maintenance
# ---------------------------------------------------------------------------

class TestLogMaintenance:
    def setup_method(self):
        self.svc = EquipmentService()

    @patch("src.services.equipment_service.db_manager")
    def test_logs_maintenance_successfully(self, mock_db):
        mock_db.select.return_value = [make_equipment_row()]  # get_equipment_by_id
        mock_db.insert.return_value = make_maintenance_row()
        result = self.svc.log_maintenance(
            equipment_id="uuid-001",
            maintenance_date=date(2024, 6, 1),
            maintenance_type=MaintenanceType.PREVENTIVE,
        )
        assert result.success is True
        assert result.data is not None

    def test_missing_equipment_id_returns_fail(self):
        result = self.svc.log_maintenance(
            equipment_id="",
            maintenance_date=date(2024, 6, 1),
            maintenance_type=MaintenanceType.PREVENTIVE,
        )
        assert result.success is False
        assert "Equipment is required" in result.error

    def test_missing_maintenance_date_returns_fail(self):
        result = self.svc.log_maintenance(
            equipment_id="uuid-001",
            maintenance_date=None,
            maintenance_type=MaintenanceType.PREVENTIVE,
        )
        assert result.success is False

    @patch("src.services.equipment_service.db_manager")
    def test_equipment_not_found_returns_fail(self, mock_db):
        mock_db.select.return_value = []  # equipment lookup fails
        result = self.svc.log_maintenance(
            equipment_id="nonexistent",
            maintenance_date=date(2024, 6, 1),
            maintenance_type=MaintenanceType.PREVENTIVE,
        )
        assert result.success is False
        assert "not found" in result.error.lower()
        mock_db.insert.assert_not_called()

    @patch("src.services.equipment_service.db_manager")
    def test_db_exception_returns_fail(self, mock_db):
        mock_db.select.return_value = [make_equipment_row()]
        mock_db.insert.side_effect = Exception("insert failed")
        result = self.svc.log_maintenance(
            equipment_id="uuid-001",
            maintenance_date=date(2024, 6, 1),
            maintenance_type=MaintenanceType.PREVENTIVE,
        )
        assert result.success is False
        assert "Could not log maintenance" in result.error
