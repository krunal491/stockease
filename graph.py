import sys
import psycopg
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QMessageBox, QLabel, QStatusBar, QHBoxLayout
)
from PyQt6.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime
from database import DB_CONFIG

class SalesGraphWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sales Performance Dashboard")
        self.resize(1000, 700)
        
        try:
            self.conn = psycopg.connect(**DB_CONFIG)
        except Exception as e:
            print("Database Connection Error:", e)
            QMessageBox.critical(self, "Error", "Failed to connect to database!")
        
        self.setup_ui()
        self.load_sales_data()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setStyleSheet("""
            QWidget {
                background-color: #F5F5F5;
                font-family: "Poppins";
            }
            QLabel {
                color: #2F4F4F;
                font-weight: bold;
            }
            QStatusBar {
                color: #666666;
                font-size: 12px;
            }
        """)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        

        header = QHBoxLayout()
        
        title = QLabel("Sales Performance Analysis")
        title.setFont(QFont("Poppins", 30, QFont.Weight.Bold))
        title.setStyleSheet("color: #2C3E50; padding: 10px;")
        header.addWidget(title, stretch=1)
        
        layout.addLayout(header)
        
        
        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas, stretch=1)
        
        
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)
    
    def refresh_data(self):
        """Public method to refresh the sales data"""
        self.load_sales_data()
    
    def load_sales_data(self):
        """Loads sales data from the database and updates the graph"""
        try:
            cursor = self.conn.cursor()
            

            cursor.execute("""
                SELECT 
                    p.name, 
                    SUM(s.quantity) as total_quantity,
                    SUM(i.total_amount) as total_revenue,
                    COUNT(s.id) as order_count
                FROM products p
                JOIN sales_orders s ON p.id = s.product_id
                JOIN invoices i ON i.sales_order_id = s.id
                GROUP BY p.name
                ORDER BY total_quantity DESC
                LIMIT 15
            """)
            
            data = cursor.fetchall()
            cursor.close()
            
            if not data:
                self.status_bar.showMessage("No sales data available")
                return
            
            products, quantities, revenues, order_counts = zip(*data)
            

            self.figure.clear()
            self.ax = self.figure.add_subplot(111)
            

            self.ax.set_facecolor('#F8F8F8')
            self.figure.patch.set_facecolor('#F5F5F5')
            

            bars = self.ax.bar(products, quantities, color='#6A1B9A', alpha=0.8)
            
          
            for bar, quantity, revenue, orders in zip(bars, quantities, revenues, order_counts):
                height = bar.get_height()
                self.ax.text(bar.get_x() + bar.get_width()/2., height,
                             f'{quantity} units\n₹{revenue:,.2f}\n{orders} orders',
                             ha='center', va='bottom', fontsize=8)
            
     
            self.ax.set_ylabel("Units Sold", fontsize=12, labelpad=10)
            self.ax.set_xlabel("Product Name", fontsize=12, labelpad=10)
            

            plt.xticks(rotation=45, ha='right', fontsize=10)
            plt.yticks(fontsize=10)
            

            self.ax.grid(axis='y', linestyle='--', alpha=0.5)
            

            self.figure.tight_layout()
            

            self.canvas.draw()
            

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            total_products = len(products)
            total_quantity = sum(quantities)
            total_revenue = sum(revenues)
            self.status_bar.showMessage(
                f"Displaying {total_products} products | "
                f"Total Sold: {total_quantity} units | "
                f"Total Revenue: ₹{total_revenue:,.2f} | "
                f"Last Updated: {timestamp}"
            )
            
        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load sales data: {e}")

    def closeEvent(self, event):
        """Clean up when window is closed"""
        if hasattr(self, 'conn'):
            self.conn.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SalesGraphWindow()
    window.show()
    sys.exit(app.exec())


