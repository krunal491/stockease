import sys
import psycopg
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, 
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from PyQt6.QtWidgets import QInputDialog
from database import DB_CONFIG


class Database:
    def __init__(self):
        try:
            self.conn = psycopg.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
        except Exception as e:
            print("Database Connection Error:", e)
            sys.exit(1)

    def fetch_products(self):
        try:
            self.cursor.execute("SELECT name, price FROM products")
            return {row[0]: row[1] for row in self.cursor.fetchall()}
        except Exception as e:
            print("Error fetching products:", e)
            return {}

    def create_sales_order(self, orders):
        try:
            successful_orders = []
            for product_name, quantity in orders.items():
                self.cursor.execute("""
                    SELECT products.id, inventory.quantity, products.price 
                    FROM products
                    JOIN inventory ON inventory.product_id = products.id
                    WHERE products.name = %s
                """, (product_name,))
                product_data = self.cursor.fetchone()

                if not product_data or len(product_data) != 3:
                    print(f"⚠️ Product '{product_name}' not found or data incomplete")
                    return None
                    
                product_id, stock_quantity, price = product_data
                
                if stock_quantity < quantity:
                    print(f"⚠️ Insufficient stock for '{product_name}' (has {stock_quantity}, needs {quantity})")
                    return None

                self.cursor.execute("""
                    INSERT INTO sales_orders (product_id, quantity, order_date)
                    VALUES (%s, %s, CURRENT_DATE)
                    RETURNING id
                """, (product_id, quantity))
                order_id = self.cursor.fetchone()[0]
                print(f"✅ Created order #{order_id} for {quantity}x {product_name}")

                self.cursor.execute("""
                    UPDATE inventory SET quantity = quantity - %s 
                    WHERE product_id = %s
                """, (quantity, product_id))
                
                if self.cursor.rowcount == 0:
                    print(f"⚠️ Failed to update inventory for product_id {product_id}!")
                    self.conn.rollback()
                    return None
                else:
                    print(f"📉 Updated inventory for {product_name} (new qty: {stock_quantity - quantity})")

                self.conn.commit()
                
                successful_orders.append((
                    product_name, 
                    quantity, 
                    price, 
                    quantity * price, 
                    order_id
                ))

            return successful_orders

        except Exception as e:
            print("💥 Database Error:", e)
            self.conn.rollback()
            return None

    def create_invoice(self, orders):
        try:
            invoice_entries = []
            for product_name, quantity, price, total_amount, order_id in orders:
                self.cursor.execute("""
                    INSERT INTO invoices (sales_order_id, total_amount) 
                    VALUES (%s, %s) RETURNING id
                """, (order_id, total_amount))
                invoice_id = self.cursor.fetchone()[0]
                invoice_entries.append((invoice_id, product_name, quantity, price, total_amount))

            self.conn.commit()
            return invoice_entries
        except Exception as e:
            print("Database Error:", e)
            self.conn.rollback()
            return None


class SalesOrderWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Sales Order & Invoice System")
        self.setGeometry(200, 200, 800, 600)

        self.setStyleSheet("""
            QWidget {
                background-color: #FFF0F5;
                font-family: "Poppins";
                font-size: 14px;
                color: gray;
            }
            QLabel {
                color: #2F4F4F;
                font-size: 18px;
                font-weight: bold;
            }
            QComboBox, QLineEdit, QListWidget {
                background-color: #F3E5F5;
                border: 2px solid #D1C4E9;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #6A1B9A;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4A148C;
            }
            QTableWidget {
                background-color: #FFFFFF;
                border: 2px solid #D1C4E9;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout()
        
   
        product_layout = QHBoxLayout()
        self.product_label = QLabel("Select Product:")
        self.product_dropdown = QComboBox()
        self.product_dropdown.setFixedWidth(250)
        self.refresh_products()

        self.quantity_label = QLabel("Quantity:")
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("Enter quantity")

        self.add_button = QPushButton("Add Product")
        self.add_button.clicked.connect(self.add_product_to_table)

        product_layout.addWidget(self.product_label)
        product_layout.addWidget(self.product_dropdown)
        product_layout.addWidget(self.quantity_label)
        product_layout.addWidget(self.quantity_input)
        product_layout.addWidget(self.add_button)


        self.product_table = QTableWidget()
        self.product_table.setColumnCount(2)
        self.product_table.setHorizontalHeaderLabels(["Product", "Quantity"])
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.product_table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)  # Enable multi-selection
        self.product_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        
        button_layout = QHBoxLayout()
        
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.setFixedSize(150, 40)
        self.delete_button.clicked.connect(self.delete_selected_products)
        
        self.clear_button = QPushButton("Clear All")
        self.clear_button.setFixedSize(150, 40)
        self.clear_button.clicked.connect(self.clear_all_products)
        
        self.order_button = QPushButton("Create Invoice")
        self.order_button.setFixedSize(150, 40)
        self.order_button.clicked.connect(self.create_sales_order)

        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.order_button)


        layout.addLayout(product_layout)
        layout.addWidget(self.product_table)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def refresh_products(self):
        """Refresh the product dropdown list"""
        current_product = self.product_dropdown.currentText()
        products = self.db.fetch_products()
        self.product_dropdown.clear()
        self.product_dropdown.addItems(products.keys())
        
  
        if current_product in products:
            index = self.product_dropdown.findText(current_product)
            if index >= 0:
                self.product_dropdown.setCurrentIndex(index)

    def add_product_to_table(self):
        """Adds selected product and quantity to the table"""
        product_name = self.product_dropdown.currentText()
        quantity_text = self.quantity_input.text()

        if not product_name or not quantity_text:
            QMessageBox.warning(self, "Warning", "Please select a product and enter a quantity!")
            return

        try:
            quantity = int(quantity_text)
            if quantity <= 0:
                QMessageBox.warning(self, "Warning", "Quantity must be a positive number!")
                return
        except ValueError:
            QMessageBox.warning(self, "Warning", "Invalid quantity entered!")
            return

       
        for row in range(self.product_table.rowCount()):
            if self.product_table.item(row, 0).text() == product_name:
                QMessageBox.warning(self, "Warning", "Product already added!")
                return

        row_position = self.product_table.rowCount()
        self.product_table.insertRow(row_position)

        product_item = QTableWidgetItem(product_name)
        product_item.setFlags(product_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.product_table.setItem(row_position, 0, product_item)

        quantity_item = QTableWidgetItem(str(quantity))
        quantity_item.setFlags(quantity_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.product_table.setItem(row_position, 1, quantity_item)

        self.quantity_input.clear()
        
    def delete_selected_products(self):
        """Delete selected products from the table"""
        selected_rows = sorted({index.row() for index in self.product_table.selectedIndexes()}, reverse=True)
        
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "No products selected!")
            return
            
        for row in selected_rows:
            self.product_table.removeRow(row)
            
    def clear_all_products(self):
        """Clear all products from the table"""
        if self.product_table.rowCount() == 0:
            return
            
        reply = QMessageBox.question(
            self, 
            "Clear All", 
            "Are you sure you want to remove all products?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.product_table.setRowCount(0)
        
    def get_customer_name(self):
        """Prompt user to enter customer name"""
        name, ok = QInputDialog.getText(self, 'Customer Information', 
                                    'Enter Customer Name:')
        if ok and name:
            return name
        return "Customer"  

    def create_sales_order(self):
        """Processes multiple selected products with their quantities"""
        orders = {}
        for row in range(self.product_table.rowCount()):
            product_name = self.product_table.item(row, 0).text()
            quantity = int(self.product_table.item(row, 1).text())
            orders[product_name] = quantity

        if not orders:
            QMessageBox.warning(self, "Warning", "No products selected!")
            return

        customer_name = self.get_customer_name()
        
        order_results = self.db.create_sales_order(orders)
        if order_results:
            invoice_results = self.db.create_invoice(order_results)
            if invoice_results:
                self.generate_invoice_pdf(invoice_results, customer_name)
                
                invoice_details = "\n".join(
                    [f"Invoice #{i[0]}: {i[1]} | Qty: {i[2]} | ₹{i[3]}" for i in invoice_results]
                )
                QMessageBox.information(self, "Success", f"Sales order and invoices created:\n\n{invoice_details}")
                self.product_table.setRowCount(0)  
            else:
                QMessageBox.warning(self, "Error", "Failed to generate invoices!")
        else:
            QMessageBox.warning(self, "Error", "Insufficient stock or invalid operation!")  

    def generate_invoice_pdf(self, invoice_results, customer_name):
        """Generates a professional-looking PDF invoice"""
        try:
            # pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))

            filename = f"Invoice_{invoice_results[0][0]}_{customer_name.replace(' ', '_')}.pdf"
            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()

            styles.add(ParagraphStyle(name='CompanyName', fontName='Helvetica', fontSize=18, alignment=1, spaceAfter=12))
            styles.add(ParagraphStyle(name='InvoiceTitle', fontName='Helvetica', fontSize=14, alignment=1, spaceAfter=6))
            styles.add(ParagraphStyle(name='Footer', fontName='Helvetica', fontSize=10, alignment=1, spaceBefore=12))

            elements = [Image("muscle_base.png", width=150, height=50)]
            elements.append(Paragraph("MuscleBase", styles["CompanyName"]))
            elements.append(Paragraph("Fueling Your Fitness Goals", styles["Italic"]))
            elements.append(Paragraph("123 Protein Lane, Fitness City, FC 12345", styles["Normal"]))
            elements.append(Paragraph("Phone: +1 234 567 890 | Email: support@musclebase.com", styles["Normal"]))
            elements.append(Spacer(1, 24))

            elements.append(Paragraph(f"Invoice #{invoice_results[0][0]}", styles["InvoiceTitle"]))
            elements.append(Paragraph(f"Bill To: {customer_name}", styles["Normal"]))
            elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", styles["Normal"]))
            elements.append(Spacer(1, 12))

            data = [["Product", "Quantity", "Price per Unit", "Total"]]
            grand_total = 0
            for invoice in invoice_results:
                invoice_id, product_name, quantity, price, total_amount = invoice
                data.append([product_name, str(quantity), f"₹{price}", f"₹{total_amount}"])
                grand_total += total_amount

            data.append(["", "", "Grand Total:", f"₹{grand_total}"])

            table = Table(data, colWidths=[200, 100, 100, 100])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#333333")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#cccccc"))
            ]))

            elements.append(table)
            elements.append(Spacer(1, 24))
            elements.append(Paragraph("Thank you for choosing MuscleBase for your nutritional needs!", styles["Footer"]))

            doc.build(elements)
            QMessageBox.information(self, "Invoice Generated", f"Invoice saved as {filename}")
        except Exception as e:
            print("PDF Generation Error:", e)
            QMessageBox.warning(self, "Error", "Failed to generate PDF invoice!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SalesOrderWindow()
    window.show()
    sys.exit(app.exec())