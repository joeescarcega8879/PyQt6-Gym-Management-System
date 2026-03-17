from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView

class SetFormat:
  
  @staticmethod
  def format_qtablewidget(qtable_widget: QTableWidget, headers: list[str], lst_data: list[tuple]) -> None:

        """
        Format a QTableWidget with headers and data.
        
        :param qtable_widget: The QTableWidget to format.
        :param headers: A list of header strings.
        :param lst_data: A list of tuples containing the data for each row.
        :raises ValueError: If data rows don't match the number of headers.
        """
        century_header_font = QFont("Century Gothic", 11, QFont.Weight.Bold)
        century_label_font = QFont("Century Gothic", 11)

        num_cols = len(headers)
        num_rows = len(lst_data)
        
        # Validate data
        if lst_data and any(len(row) != num_cols for row in lst_data):
            raise ValueError(f"All data rows must have {num_cols} columns to match headers")

        # Setup table
        qtable_widget.setColumnCount(num_cols)
        qtable_widget.setRowCount(num_rows)
        qtable_widget.setHorizontalHeaderLabels(headers)
        
        # Behavior configuration
        qtable_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        qtable_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        qtable_widget.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Header configuration
        qtable_widget.horizontalHeader().setFont(century_header_font)
        qtable_widget.verticalHeader().hide()
        qtable_widget.setShowGrid(False)

        # Populate data
        for row in range(num_rows):

            row_color = QColor("#f0f0f0") if row % 2 == 0 else QColor("#ffffff")

            for column in range(num_cols):
                item = QTableWidgetItem(str(lst_data[row][column]))
                item.setBackground(row_color)
                item.setFont(century_label_font)
                qtable_widget.setItem(row, column, item)

        # Resize columns and rows to fit contents
        for column in range(num_cols):
            qtable_widget.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

        qtable_widget.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
