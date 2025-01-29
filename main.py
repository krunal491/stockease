import sys
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtCore import QFile, QTextStream
import resources_rc

from dashboard import Ui_MainWindow
from product import ProductWindow
from inventory import InventoryWindow
from salesorder import SalesOrderWindow
from Purchase_Order import PurchaseWindow
# from order_item import OrderItemWindow
from graph import SalesGraphWindow
from return_refund import ReturnRefundWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

  
        self.ui.icon_only_widget.hide()
        # Clean up placeholder pages from Qt Designer
        while self.ui.stackedWidget.count() > 0:
            self.ui.stackedWidget.removeWidget(self.ui.stackedWidget.widget(0))

        self.initialize_windows()
        self.add_widgets_to_stack()
        
        # Set Dashboard as the initial page
        self.ui.stackedWidget.setCurrentWidget(self.dashboard_window)
        self.ui.dashboard_btn_2.setChecked(True)

        self.connect_navigation_buttons()

        self.ui.stackedWidget.currentChanged.connect(self.on_page_changed)

    def initialize_windows(self):
        """Initialize all application windows"""
        self.product_window = ProductWindow(self)
        self.inventory_window = InventoryWindow(self)
        self.salesorder_window = SalesOrderWindow(self)
        self.purchaseorder_window = PurchaseWindow(self)
        # self.salesitem_window = SalesItemWindow(self)
        self.dashboard_window = SalesGraphWindow(self)
        self.return_refund_window = ReturnRefundWindow(self)

    def add_widgets_to_stack(self):
        """Add all windows to stacked widget"""
        self.ui.stackedWidget.addWidget(self.product_window)
        self.ui.stackedWidget.addWidget(self.inventory_window)
        self.ui.stackedWidget.addWidget(self.salesorder_window)
        self.ui.stackedWidget.addWidget(self.purchaseorder_window)
        # self.ui.stackedWidget.addWidget(self.salesitem_window)
        self.ui.stackedWidget.addWidget(self.dashboard_window)
        self.ui.stackedWidget.addWidget(self.return_refund_window)

    def connect_navigation_buttons(self):
        """Connect all navigation buttons to their respective windows"""
        self.ui.dashborad_btn_1.clicked.connect(self.show_dashboard_window)
        self.ui.dashboard_btn_2.clicked.connect(self.show_dashboard_window)

        self.ui.products_btn_1.clicked.connect(self.show_product_window)
        self.ui.products_btn_2.clicked.connect(self.show_product_window)

        self.ui.inventory_btn_1.clicked.connect(self.show_inventory_window)
        self.ui.inventory_btn_2.clicked.connect(self.show_inventory_window)

        self.ui.salesorder_btn_1.clicked.connect(self.show_salesorder_window)
        self.ui.salesorder_btn_2.clicked.connect(self.show_salesorder_window)

        self.ui.purchase_btn_1.clicked.connect(self.show_purchaseorder_window)
        self.ui.purchase_btn_2.clicked.connect(self.show_purchaseorder_window)

        

        self.ui.return_btn_1.clicked.connect(self.show_return_window)
        self.ui.return_btn_2.clicked.connect(self.show_return_window)

    def on_page_changed(self, index):
        """Automatically refresh dashboard or inventory when they become visible"""
        current_widget = self.ui.stackedWidget.currentWidget()
        if current_widget == self.dashboard_window:
            self.dashboard_window.refresh_data()
        elif current_widget == self.inventory_window:
            self.inventory_window.load_inventory()  

    def show_dashboard_window(self):
        self.ui.stackedWidget.setCurrentWidget(self.dashboard_window)
        self.dashboard_window.refresh_data()

    def show_product_window(self):
        self.ui.stackedWidget.setCurrentWidget(self.product_window)

    def show_inventory_window(self):
        self.ui.stackedWidget.setCurrentWidget(self.inventory_window)

    def show_salesorder_window(self):
        self.ui.stackedWidget.setCurrentWidget(self.salesorder_window)

    def show_purchaseorder_window(self):
        self.ui.stackedWidget.setCurrentWidget(self.purchaseorder_window)

    def show_salesitem_window(self):
        self.ui.stackedWidget.setCurrentWidget(self.salesitem_window)

    def show_return_window(self):
        self.ui.stackedWidget.setCurrentWidget(self.return_refund_window)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    style_file = QFile("style.qss")
    if style_file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
        style_stream = QTextStream(style_file)
        app.setStyleSheet(style_stream.readAll())
        style_file.close()

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


