import sys
import psycopg
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QMessageBox, QFormLayout, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database import DB_CONFIG


APP_STYLESHEET = """
    QWidget {
        background-color: #f4f4f4;
        font-family: 'Arial';
        color: #333; /* Ensure default text color */
    }
    QLabel {
        font-size: 14px;
        color: #333; /* Explicitly set text color */
    }
    QLabel#title {
        font-size: 18px;
        font-weight: bold;
        color: #2c3e50;
    }
    QComboBox, QLineEdit {
        background-color: #fff;
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 8px;
        font-size: 14px;
        color: #333; /* Ensure text is visible */
    }
    QComboBox:hover, QLineEdit:hover {
        border: 1px solid #3498db;
    }
    QPushButton {
        background-color: #3498db;
        color: white; /* Button text color */
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #2980b9;
    }
    QPushButton:pressed {
        background-color: #1c5980;
    }
    QMessageBox {
        background-color: #f4f4f4;
    }
    QMessageBox QLabel {
        font-size: 14px;
        color: #333; /* Ensure text is visible in message boxes */
    }
"""

class ReturnRefundWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Returns Management")
        self.setGeometry(320, 120, 500, 350)
        self.setStyleSheet(APP_STYLESHEET) 
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Initialize the UI layout and components."""
        layout = QVBoxLayout()
        layout.setSpacing(15) 


        title = QLabel("Returns Management")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)


        returns_layout = QFormLayout()
        returns_layout.setSpacing(10)
        
        self.sales_order_dropdown = self.create_dropdown("Select Sales Order")
        self.product_dropdown = self.create_dropdown("Select Product")
        self.price_input = self.create_input("Price", read_only=True)
        self.quantity_input = self.create_input("Enter Quantity")
        self.return_reason_input = self.create_input("Enter Return Reason")
        self.return_button = self.create_button("Process Return", self.process_return)

        returns_layout.addRow("Sales Order:", self.sales_order_dropdown)
        returns_layout.addRow("Product:", self.product_dropdown)
        returns_layout.addRow("Price:", self.price_input)
        returns_layout.addRow("Quantity:", self.quantity_input)
        returns_layout.addRow("Return Reason:", self.return_reason_input)
        returns_layout.addRow(self.return_button)


        self.sales_order_dropdown.currentIndexChanged.connect(self.on_sales_order_selected)
        self.product_dropdown.currentIndexChanged.connect(self.on_product_selected)


        layout.addLayout(returns_layout)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.setLayout(layout)

    def create_dropdown(self, placeholder_text):
        """Helper function to create a dropdown."""
        dropdown = QComboBox()
        dropdown.setPlaceholderText(placeholder_text)
        dropdown.setToolTip(f"Select a {placeholder_text} from the list.")
        return dropdown

    def create_input(self, placeholder_text, read_only=False):
        """Helper function to create a line edit input field."""
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder_text)
        input_field.setToolTip(f"Enter the {placeholder_text}.")
        if read_only:
            input_field.setReadOnly(True)
        return input_field

    def create_button(self, text, callback):
        """Helper function to create a button and assign its callback function."""
        button = QPushButton(text)
        button.clicked.connect(callback)
        button.setToolTip(f"Click to {text.lower()}.")
        return button

    def get_db_connection(self):
        """Establish and return a database connection."""
        try:
            conn = psycopg.connect(**DB_CONFIG)
            print("Database connection successful!")
            return conn
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to connect to database:\n{e}")
            sys.exit(1)

    def load_data(self):
        """Load dropdown data from the database."""
        self.populate_dropdown(self.sales_order_dropdown, "SELECT id FROM sales_orders")

    def populate_dropdown(self, dropdown, query, params=None, format_func=lambda x: str(x[0])):
        """Fetch data from the database and populate the dropdown."""
        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            results = cursor.fetchall()
            print(f"Fetched data: {results}")

            dropdown.clear()
            dropdown.addItems([format_func(result) for result in results])

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to fetch data:\n{e}")

        finally:
            cursor.close()
            conn.close()

    def on_sales_order_selected(self):
        """Update the product dropdown when a sales order is selected."""
        order_id = self.sales_order_dropdown.currentText()
        if not order_id:
            return


        query = """
            SELECT p.name 
            FROM sales_orders so
            JOIN products p ON so.product_id = p.id
            WHERE so.id = %s
        """
        self.populate_dropdown(self.product_dropdown, query, (order_id,))

    def on_product_selected(self):
        """Fetch and display the price of the selected product."""
        product_name = self.product_dropdown.currentText().strip()
        if not product_name:
            self.price_input.clear()
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT price FROM products WHERE name = %s", (product_name,))
            price_result = cursor.fetchone()
            if price_result:
                self.price_input.setText(str(price_result[0]))
            else:
                self.price_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to fetch product price:\n{e}")
        finally:
            cursor.close()
            conn.close()

    def process_return(self):
        """Process return for selected sales order and product, updating inventory."""
        order_id = self.sales_order_dropdown.currentText().strip()
        product_name = self.product_dropdown.currentText().strip()
        quantity = self.quantity_input.text().strip()
        return_reason = self.return_reason_input.text().strip()

        if not order_id or not product_name:
            QMessageBox.warning(self, "Warning", "Please select a valid Sales Order and Product.")
            return

        if not quantity.isdigit():
            QMessageBox.warning(self, "Warning", "Quantity must be a valid number.")
            return

        quantity = int(quantity)
        if quantity <= 0:
            QMessageBox.warning(self, "Warning", "Quantity must be greater than zero.")
            return

        conn = self.get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN")


            cursor.execute("SELECT id FROM products WHERE name = %s", (product_name,))
            product_result = cursor.fetchone()
            if not product_result:
                QMessageBox.warning(self, "Warning", "Selected product does not exist.")
                return
            product_id = product_result[0]


            cursor.execute(
                "SELECT quantity FROM sales_orders WHERE id = %s AND product_id = %s",
                (order_id, product_id)
            )
            sales_order_result = cursor.fetchone()
            if not sales_order_result:
                QMessageBox.warning(self, "Warning", "Selected product is not part of the chosen Sales Order.")
                return

            ordered_quantity = sales_order_result[0]
            if quantity > ordered_quantity:
                QMessageBox.warning(self, "Warning", f"Return quantity ({quantity}) cannot exceed ordered quantity ({ordered_quantity}).")
                return


            cursor.execute(
                "INSERT INTO returns (sales_order_id, product_id, quantity, return_reason) VALUES (%s, %s, %s, %s) RETURNING id",
                (order_id, product_id, quantity, return_reason)
            )
            return_id = cursor.fetchone()[0]


            cursor.execute(
                """
                INSERT INTO inventory (product_id, quantity, last_order_date)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (product_id) DO UPDATE 
                SET quantity = inventory.quantity + EXCLUDED.quantity,
                    last_order_date = CURRENT_TIMESTAMP;
                """,
                (product_id, quantity)
            )

            conn.commit()
            QMessageBox.information(self, "Success", "Return processed successfully! Inventory updated.")
            self.load_data()  

        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to process return:\n{e}")

        finally:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReturnRefundWindow()
    window.show()
