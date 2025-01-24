# ... [imports remain unchanged]
import sys
import psycopg
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QMessageBox,
    QComboBox, QLineEdit, QHBoxLayout, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database import DB_CONFIG


class Database:
    def __init__(self):
        try:
            self.conn = psycopg.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            self.initialize_tables()
        except psycopg.Error as e:
            QMessageBox.critical(None, "Database Error", f"Failed to connect to database: {e}\nPlease ensure PostgreSQL is running.")
            sys.exit(1)

    def initialize_tables(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER REFERENCES products(id),
                    quantity INTEGER NOT NULL,
                    order_date DATE NOT NULL,
                    executed BOOLEAN DEFAULT FALSE
                )
            """)
            self.conn.commit()
        except Exception as e:
            print("Error initializing tables:", e)
            self.conn.rollback()

    def fetch_categories(self):
        self.cursor.execute("SELECT id, name FROM categories")
        return self.cursor.fetchall()

    def fetch_products_by_category(self, category_id):
        self.cursor.execute("SELECT id, name FROM products WHERE category_id = %s", (category_id,))
        return self.cursor.fetchall()

    def fetch_inventory(self):
        self.cursor.execute("""
            SELECT i.id, c.name AS category, p.name AS product, i.quantity, i.last_order_date 
            FROM inventory i 
            JOIN products p ON i.product_id = p.id
            JOIN categories c ON p.category_id = c.id
        """)
        return self.cursor.fetchall()

    def fetch_purchases(self):
        """Now includes both executed and unexecuted orders"""
        self.cursor.execute("""
            SELECT po.id, c.name AS category, p.name AS product, po.quantity, po.order_date, po.executed
            FROM purchase_orders po
            JOIN products p ON po.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            ORDER BY po.id DESC
        """)
        return self.cursor.fetchall()

    def add_inventory_item(self, product_id, quantity):
        try:
            self.cursor.execute("""
                INSERT INTO inventory (product_id, quantity, last_order_date) 
                VALUES (%s, %s, CURRENT_DATE) 
                ON CONFLICT (product_id) DO UPDATE 
                SET quantity = inventory.quantity + EXCLUDED.quantity, 
                    last_order_date = CURRENT_DATE
            """, (product_id, quantity))
            self.conn.commit()
            return True
        except Exception as e:
            print("Database Error (add_inventory_item):", e)
            self.conn.rollback()
            return False

    def add_purchase_order(self, product_id, quantity):
        try:
            self.cursor.execute("""
                INSERT INTO purchase_orders (product_id, quantity, order_date, executed) 
                VALUES (%s, %s, CURRENT_DATE, FALSE)
            """, (product_id, quantity))
            self.conn.commit()
            return True
        except Exception as e:
            print("Database Error (add_purchase_order):", e)
            self.conn.rollback()
            return False

    def execute_purchase_order(self, purchase_ids):
        try:
            self.cursor.execute("""
                SELECT product_id, quantity FROM purchase_orders 
                WHERE id = ANY(%s) AND executed = FALSE
            """, (purchase_ids,))
            orders = self.cursor.fetchall()

            if not orders:
                return False

            for product_id, quantity in orders:
                if not self.add_inventory_item(product_id, quantity):
                    return False

            self.cursor.execute("""
                UPDATE purchase_orders 
                SET executed = TRUE 
                WHERE id = ANY(%s)
            """, (purchase_ids,))
            self.conn.commit()
            return True
        except Exception as e:
            print("Database Error (execute_purchase_order):", e)
            self.conn.rollback()
            return False

    def remove_purchase_orders(self, purchase_ids):
        try:
            self.cursor.execute("DELETE FROM purchase_orders WHERE id = ANY(%s)", (purchase_ids,))
            self.conn.commit()
            return True
        except Exception as e:
            print("Database Error (remove_purchase_orders):", e)
            self.conn.rollback()
            return False


class PurchaseWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.setWindowTitle("Purchase Management")
        self.setGeometry(100, 100, 900, 600)

        main_layout = QVBoxLayout()

        title_label = QLabel("🛒 Purchase Orders")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 30px; font-weight: bold; color:black;")
        title_label.setFont(QFont("Poppins", 24, QFont.Weight.Bold))


        self.purchase_table = QTableWidget()
        self.purchase_table.setColumnCount(6)
        self.purchase_table.setHorizontalHeaderLabels(["ID", "Category", "Product", "Quantity", "Order Date", "Execute"])
        self.purchase_table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
        self.purchase_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        from PyQt6.QtWidgets import QHeaderView

        self.purchase_table.horizontalHeader().setStretchLastSection(True)
        self.purchase_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.purchase_table.setAlternatingRowColors(True)
        self.purchase_table.setColumnWidth(0, 150)
        self.purchase_table.hideColumn(0)

        self.purchase_table.setStyleSheet("""
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
            QTableWidget::item:selected {
                background-color: #D1C4E9;
                color: black;
            }
        """)

        self.load_purchases()

        dropdown_layout = QHBoxLayout()
        dropdown_layout.setSpacing(10)

        self.category_dropdown = QComboBox()
        self.category_dropdown.addItem("Select Category", -1)
        self.category_dropdown.currentIndexChanged.connect(self.load_products)
        self.style_dropdown(self.category_dropdown)
        dropdown_layout.addWidget(self.category_dropdown)

        self.product_dropdown = QComboBox()
        self.product_dropdown.addItem("Select Product", -1)
        self.style_dropdown(self.product_dropdown)
        dropdown_layout.addWidget(self.product_dropdown)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Enter Qty")
        self.quantity_input.setFixedWidth(100)
        self.quantity_input.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 8px;
                color: black;
                background-color: #EDE7F6;
                border: 2px solid #6A1B9A;
                border-radius: 6px;
            }
        """)
        button_layout.addWidget(self.quantity_input)

        place_order_btn = QPushButton("Place Order")
        place_order_btn.setFixedSize(160, 50)
        place_order_btn.setStyleSheet(self.button_style("#4A148C", "#5C46A0"))
        place_order_btn.clicked.connect(self.place_purchase_order)
        button_layout.addWidget(place_order_btn)

        execute_order_btn = QPushButton("Execute Order")
        execute_order_btn.setFixedSize(160, 50)
        execute_order_btn.setStyleSheet(self.button_style("#2E7D32", "#1B5E20"))
        execute_order_btn.clicked.connect(self.execute_purchase_order)
        button_layout.addWidget(execute_order_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.setFixedSize(160, 50)
        remove_btn.setStyleSheet(self.button_style("#E53935", "#C62828"))
        remove_btn.clicked.connect(self.remove_selected_purchases)
        button_layout.addWidget(remove_btn)

        main_layout.addWidget(title_label)
        main_layout.addWidget(self.purchase_table)
        main_layout.addLayout(dropdown_layout)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        self.load_categories()

    def button_style(self, color, hover_color):
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

    def style_dropdown(self, dropdown):
        dropdown.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                padding: 6px 10px;
                color: black;
                background-color: white;
                border: 2px solid #6A1B9A;
                border-radius: 6px;
            }

            QComboBox:hover {
                border: 2px solid #512DA8;
            }

            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left-width: 1px;
                border-left-color: #6A1B9A;
                border-left-style: solid;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background-color: #D1C4E9;
            }

            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #6A1B9A;
                selection-background-color: #EDE7F6;
                selection-color: black;
            }
        """)

    def load_categories(self):
        self.category_dropdown.clear()
        self.category_dropdown.addItem("Select Category", -1)
        categories = self.db.fetch_categories()
        for category_id, name in categories:
            self.category_dropdown.addItem(name, category_id)
        self.load_products()

    def load_products(self):
        self.product_dropdown.clear()
        self.product_dropdown.addItem("Select Product", -1)
        category_id = self.category_dropdown.currentData()
        if category_id != -1:
            products = self.db.fetch_products_by_category(category_id)
            for product_id, name in products:
                self.product_dropdown.addItem(name, product_id)

    def load_purchases(self):
        self.purchase_table.setRowCount(0)
        purchase_orders = self.db.fetch_purchases()
        for row_idx, item in enumerate(purchase_orders):
            self.purchase_table.insertRow(row_idx)
            for col_idx, value in enumerate(item):
                if col_idx == 4:
                    value = value.strftime("%Y-%m-%d") if value else "N/A"
                elif col_idx == 5:
                    value = "Executed" if value else "Not Execute"
                self.purchase_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def place_purchase_order(self):
        product_id = self.product_dropdown.currentData()
        quantity_text = self.quantity_input.text()

        if product_id == -1:
            QMessageBox.warning(self, "⚠️ Warning", "Please select a valid product!")
            return

        if not quantity_text.isdigit() or int(quantity_text) <= 0:
            QMessageBox.warning(self, "⚠️ Warning", "Please enter a valid positive quantity!")
            return

        quantity = int(quantity_text)
        if self.db.add_purchase_order(product_id, quantity):
            self.load_purchases()
            self.quantity_input.clear()
            QMessageBox.information(self, "✅ Success", "Purchase order placed successfully!")
        else:
            QMessageBox.warning(self, "⚠️ Error", "Failed to place purchase order!")

    def execute_purchase_order(self):
        selected_rows = self.purchase_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "⚠️ Warning", "No orders selected!")
            return

        purchase_ids = []
        for row in selected_rows:
            status = self.purchase_table.item(row.row(), 5).text()
            if status == "Not Execute":
                purchase_id = int(self.purchase_table.item(row.row(), 0).text())
                purchase_ids.append(purchase_id)

        if not purchase_ids:
            QMessageBox.information(self, "ℹ️ Info", "Selected orders are already executed.")
            return

        confirmation = QMessageBox.question(
            self, "Confirm Execution",
            f"Execute {len(purchase_ids)} selected orders and add to inventory?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirmation == QMessageBox.StandardButton.Yes:
            if self.db.execute_purchase_order(purchase_ids):
                self.load_purchases()
                QMessageBox.information(self, "✅ Success", "Orders executed successfully!")
            else:
                QMessageBox.warning(self, "⚠️ Error", "Failed to execute orders!")

    def remove_selected_purchases(self):
        selected_rows = self.purchase_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "⚠️ Warning", "No orders selected!")
            return

        confirmation = QMessageBox.question(
            self, "Confirm Deletion",
            f"Delete {len(selected_rows)} selected orders?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirmation == QMessageBox.StandardButton.Yes:
            purchase_ids = [int(self.purchase_table.item(row.row(), 0).text()) for row in selected_rows]
            if self.db.remove_purchase_orders(purchase_ids):
                self.load_purchases()
                QMessageBox.information(self, "✅ Success", "Orders deleted successfully!")
            else:
                QMessageBox.warning(self, "⚠️ Error", "Failed to delete orders!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PurchaseWindow()
    window.show()
    sys.exit(app.exec())
