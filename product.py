import sys
import psycopg
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QTableWidget,
    QMessageBox, QDialog, QComboBox, QLineEdit, QHBoxLayout, QTableWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database import DB_CONFIG


class Database:
    def __init__(self):
        try:
            self.conn = psycopg.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
        except psycopg.Error as e:
            QMessageBox.critical(None, "Database Error", f"Failed to connect to database: {e}\nPlease ensure PostgreSQL is running.")
            sys.exit(1)

    def fetch_products(self):
        self.cursor.execute("""
            SELECT categories.name, products.name, products.price
            FROM products
            JOIN categories ON products.category_id = categories.id
            ORDER BY categories.name, products.name
        """)
        return self.cursor.fetchall()

    def fetch_categories(self):
        self.cursor.execute("SELECT name FROM categories ORDER BY name")
        return [row[0] for row in self.cursor.fetchall()]

    def add_product(self, product_name, category_name, price):
        try:

            self.cursor.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
            category_id = self.cursor.fetchone()
            
            if not category_id:
                QMessageBox.critical(None, "Error", "Category not found!")
                return False
                

            self.cursor.execute(
                "INSERT INTO products (name, category_id, price) VALUES (%s, %s, %s) RETURNING id",
                (product_name, category_id[0], price)
            )
            product_id = self.cursor.fetchone()[0]
            
            # Automatically add to inventory with 0 quantity
            self.cursor.execute(
                "INSERT INTO inventory (product_id, quantity, last_order_date) VALUES (%s, 0, CURRENT_DATE)",
                (product_id,)
            )

            self.conn.commit()
            return True
        except psycopg.IntegrityError:
            QMessageBox.critical(None, "Error", "Product already exists!")
            self.conn.rollback()
            return False
        except psycopg.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error adding product: {e}")
            self.conn.rollback()
            return False

    def remove_product(self, product_name):
        try:
            self.cursor.execute("DELETE FROM products WHERE name = %s", (product_name,))
            self.conn.commit()
            return True
        except psycopg.Error as e:
            QMessageBox.critical(None, "Database Error", f"Error removing product: {e}")
            self.conn.rollback()
            return False

    def close(self):
        self.cursor.close()
        self.conn.close()


class ProductWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.setWindowTitle("Product Management")
        self.setGeometry(300, 200, 700, 450)
        self.setStyleSheet(self.load_styles())

        layout = QVBoxLayout()

        self.title_label = QLabel("\U0001F4E6 Manage Products")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setFont(QFont("Poppins", 26, QFont.Weight.Bold))


        self.product_table = QTableWidget()
        self.product_table.setColumnCount(3)
        self.product_table.setHorizontalHeaderLabels(["CATEGORY", "PRODUCT", "PRICE"])
        self.product_table.setColumnWidth(0, 300)
        self.product_table.setColumnWidth(1, 300)
        self.product_table.setColumnWidth(2, 150)
        self.product_table.verticalHeader().setDefaultSectionSize(40)
        self.load_products()


        header_font = QFont("Arial", 14, QFont.Weight.Bold)
        self.product_table.horizontalHeader().setFont(header_font)


        self.add_button = QPushButton("Add Product")
        self.add_button.clicked.connect(self.add_product)

        self.remove_button = QPushButton("Remove Product")
        self.remove_button.clicked.connect(self.remove_product)


        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)

        layout.addWidget(self.title_label)
        layout.addWidget(self.product_table)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_styles(self):
        """Load external CSS styling."""
        return """
        QWidget {
            background-color: #A98FEF; 
            color: #FFFFFF;  
        }
        QLabel {
            font-size: 18px;
            font-weight: bold;
            color: #FFFFFF;
        }
        QLabel#titleLabel {
            font-size: 24px;
            font-weight: bold;
            color: #FFFFFF;
        }
        QPushButton {
            background-color: #9370DB; 
            color: white;
            font-size: 16px;
            border-radius: 8px;
            font-weight: bold;
            padding: 10px 15px;
            border: 2px solid #7A5DC7;
            transition: background-color 0.3s ease, border-color 0.3s ease;
        }
        QPushButton:hover {
            background-color: #7A5DC7;
            border-color: #6845B0;
            font-weight: bold;
        }
        QTableWidget {
            background-color: #FFFFFF;
            border: 1px solid #ccc;
            gridline-color: #7A5DC7;
            text-align:center;
            font-size: 18px;
            color: #000000;
        }
        QTableWidget::item {
            padding: 10px;
        }
        QHeaderView::section {
            background-color: #7A5DC7;
            color: white;
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
            border: 1px solid #5A4DB0;
        }
        """

    def load_products(self):
        """Refresh the table with category, product names, and price."""
        self.product_table.setRowCount(0)
        products = self.db.fetch_products()

        for row_index, (category_name, product_name, price) in enumerate(products):
            self.product_table.insertRow(row_index)
            self.product_table.setItem(row_index, 0, QTableWidgetItem(category_name))
            self.product_table.setItem(row_index, 1, QTableWidgetItem(product_name))
            self.product_table.setItem(row_index, 2, QTableWidgetItem(f"₹{price:.2f}"))

    def add_product(self):
        categories = self.db.fetch_categories()
        if not categories:
            QMessageBox.warning(self, "⚠️ Warning", "No categories available! Please add a category first.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Product")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout()

        category_label = QLabel("Select Category:")
        category_dropdown = QComboBox()
        category_dropdown.addItems(categories)

        product_label = QLabel("Enter Product Name:")
        product_input = QLineEdit()

        price_label = QLabel("Enter Price:")
        price_input = QLineEdit()
        price_input.setPlaceholderText("Enter price in ₹")

        confirm_button = QPushButton("Confirm")
        confirm_button.clicked.connect(dialog.accept)

        layout.addWidget(category_label)
        layout.addWidget(category_dropdown)
        layout.addWidget(product_label)
        layout.addWidget(product_input)
        layout.addWidget(price_label)
        layout.addWidget(price_input)
        layout.addWidget(confirm_button)
        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            product_name = product_input.text().strip()
            selected_category = category_dropdown.currentText()
            price_text = price_input.text().strip()

            if not product_name:
                QMessageBox.warning(self, "⚠️ Warning", "Product name cannot be empty!")
                return

            try:
                price = float(price_text)
                if price < 0:
                    QMessageBox.warning(self, "⚠️ Warning", "Price cannot be negative!")
                    return
            except ValueError:
                QMessageBox.warning(self, "⚠️ Warning", "Invalid price! Please enter a valid number.")
                return

            if self.db.add_product(product_name, selected_category, price):
                QMessageBox.information(self, "✅ Success", "Product added successfully!")
                self.load_products()

    def remove_product(self):
        selected_row = self.product_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "⚠️ Warning", "Please select a product to remove.")
            return

        product_name = self.product_table.item(selected_row, 1).text()
        
        reply = QMessageBox.question(
            self, 
            "Confirm Removal",
            f"Are you sure you want to remove '{product_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.remove_product(product_name):
                self.load_products()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProductWindow()
    window.show()
    sys.exit(app.exec())