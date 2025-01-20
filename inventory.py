import sys
import psycopg
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QMessageBox,
    QComboBox, QLineEdit, QHBoxLayout, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor


from database import DB_CONFIG

class Database:
    def __init__(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
        except psycopg.Error as e:
            QMessageBox.critical(None, "Database Error", f"Failed to connect to database: {e}\nPlease ensure PostgreSQL is running.")
            sys.exit(1)

    def fetch_categories(self):
        """Fetch categories from the categories table"""
        self.cursor.execute("SELECT id, name FROM categories")
        return self.cursor.fetchall()

    def fetch_products_by_category(self, category_id):
        """Fetch products based on the selected category"""
        self.cursor.execute("SELECT id, name FROM products WHERE category_id = %s", (category_id,))
        return self.cursor.fetchall()

    def fetch_inventory(self):
        """Fetch inventory items from the inventory table, excluding price"""
        self.cursor.execute("""
            SELECT i.id, c.name AS category, p.name AS product, i.quantity, i.last_order_date 
            FROM inventory i 
            JOIN products p ON i.product_id = p.id
            JOIN categories c ON p.category_id = c.id
        """)
        return self.cursor.fetchall()

    def add_inventory_item(self, product_id, quantity):
        """Add or update inventory item, excluding price"""
        try:
            self.cursor.execute(
                """
                INSERT INTO inventory (product_id, quantity, last_order_date) 
                VALUES (%s, %s, CURRENT_DATE) 
                ON CONFLICT (product_id) DO UPDATE 
                SET quantity = inventory.quantity + EXCLUDED.quantity, 
                    last_order_date = CURRENT_DATE
                """,
                (product_id, quantity)
            )
            self.conn.commit()
        except Exception as e:
            print("Database Error:", e)
            self.conn.rollback()

    def remove_inventory_items(self, inventory_ids):
        """Removes multiple selected inventory items"""
        try:
            query = "DELETE FROM inventory WHERE id = ANY(%s)"
            self.cursor.execute(query, (inventory_ids,))
            self.conn.commit()
        except Exception as e:
            print("Database Error:", e)
            self.conn.rollback()


class InventoryWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.db = Database()  

        self.setWindowTitle("Inventory Management")
        self.setGeometry(100, 100, 900, 600)

        main_layout = QVBoxLayout()

        title_label = QLabel("📦 Inventory Items")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 30px; font-weight: bold; color:black;")
        title_label.setFont(QFont("Poppins", 24, QFont.Weight.Bold))

        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(5)  
        self.inventory_table.setHorizontalHeaderLabels(["ID", "Category", "Product", "Quantity", "Last Order"])
        self.inventory_table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
        self.inventory_table.setColumnWidth(0, 150)
        self.inventory_table.setColumnWidth(1, 150)
        self.inventory_table.setColumnWidth(2, 150)
        self.inventory_table.setColumnWidth(3, 150)
        self.inventory_table.setColumnWidth(4, 150)
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.inventory_table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;
                background-color: #E0FFFF;
                color: black;
                border: 2px solid #D1C4E9;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #6A1B9A;
                color: white;
                padding: 10px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item {
                padding:8px;
                
            }
            QTableWidget::item:selected {
                background-color: #D1C4E9;
                color: black;
            }
            QTableWidget::item:alternate {
                background-color: #F3E5F5;
            }
        """)
        self.inventory_table.setAlternatingRowColors(True) 
        self.inventory_table.hideColumn(0)  
        self.load_inventory()

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        remove_button = QPushButton("Remove Selected")
        remove_button.setFixedSize(160, 50)
        remove_button.setStyleSheet(self.button_style("#E53935", "#C62828"))
        remove_button.clicked.connect(self.remove_selected_inventory)
        button_layout.addWidget(remove_button)

        main_layout.addWidget(title_label)
        main_layout.addWidget(self.inventory_table)
        main_layout.addWidget(button_container)

        self.setLayout(main_layout)
    def showEvent(self, event):
        """Override showEvent to refresh data when the window is shown"""
        super().showEvent(event)
        self.load_inventory()

    def button_style(self, color, hover_color):
        """Returns button styles with dynamic colors."""
        return f"""
            QPushButton {{
                font-size: 14px;
                font-weight: bold;
                background-color: {color};
                border-radius: 6px;
                padding: 8px;
                color: white;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """

    def load_inventory(self):
        """Fetches inventory from PostgreSQL and displays in the table."""
        self.inventory_table.setRowCount(0)
        inventory_items = self.db.fetch_inventory()
        
        for row_idx, item in enumerate(inventory_items):
            self.inventory_table.insertRow(row_idx)
            for col_idx, value in enumerate(item):
                if col_idx == 4:  
                    value = value.strftime("%Y-%m-%d") if value else "N/A"
                self.inventory_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def remove_selected_inventory(self):
        """Removes multiple selected inventory items"""
        selected_rows = self.inventory_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "⚠️ Warning", "No items selected!")
            return

        confirmation = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_rows)} selected items?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirmation == QMessageBox.StandardButton.Yes:
            inventory_ids = [int(self.inventory_table.item(row.row(), 0).text()) for row in selected_rows]
            self.db.remove_inventory_items(inventory_ids)
            self.load_inventory()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InventoryWindow()
    window.show()
    sys.exit(app.exec())