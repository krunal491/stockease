# Stockease

Stockease is a desktop-based inventory and stock management application designed to manage products, inventory, sales, purchases, returns/refunds, and business reporting. Built with Python and PyQt6, the application provides a centralized desktop interface with a PostgreSQL database backend for retail and stock-keeping workflows.

---

## Features

Stockease includes the following core functionalities implemented across its desktop views and database services:

* **Product Management (`product.py`)**:
  * Browse products organized by category with pricing.
  * Add new products with category assignment, unit pricing, and automatic initial inventory registration.
  * Delete existing products from the catalog with database synchronization.

* **Inventory & Stock Management (`inventory.py`)**:
  * Real-time stock visibility displaying product name, category, available quantity, and last order date.
  * Restock existing items with automatic quantity updates (`ON CONFLICT` resolution).
  * Filter and query stock by product category.
  * Multi-selection and bulk removal of inventory records.

* **Sales Order Management (`salesorder.py`)**:
  * Create customer sales orders with live product selection and unit price resolution.
  * Pre-sale stock validation to prevent processing orders with insufficient inventory.
  * Atomic inventory deduction upon order confirmation.
  * Automated itemized invoice creation stored in the database.
  * Professional PDF invoice generation via ReportLab with order timestamps, line items, and total calculation.

* **Purchase Order Management (`Purchase_Order.py`)**:
  * Create supplier purchase orders for inventory replenishment.
  * Track order statuses (pending vs. executed).
  * Execute purchase orders to automatically increment stock quantities in the inventory table.

* **Returns and Refunds (`return_refund.py`)**:
  * Process customer return requests against existing sales orders.
  * Validation of return quantities against original order quantities.
  * Logging of return reason and timestamp.
  * Automatic inventory quantity restoration upon return processing.

* **Dashboard & Visual Reporting (`graph.py`, `dashboard.py`)**:
  * Interactive sales performance analytics embedded directly into the PyQt6 desktop interface using Matplotlib.
  * Bar chart visualization showing top-selling products by units sold.
  * Numerical annotations on chart bars displaying units sold, total revenue in INR (₹), and total order count per product.
  * Real-time status bar aggregating total catalog items analyzed, total units sold, cumulative revenue, and refresh timestamps.
  * Auto-refreshing metrics on view activation.

* **Desktop UI & Navigation (`main.py`, `sidebar.ui`, `style.qss`)**:
  * Collapsible sidebar navigation featuring both expanded (icon + text) and compact (icon-only) modes.
  * Dark-themed navigation styling with interactive hover and active states via Qt Style Sheets (QSS).
  * Central `QStackedWidget` architecture enabling seamless transitions between modules without reopening windows.

* **Authentication & User Management (`front_page.py`, `database.py`)**:
  * Login and registration screen with animated UI transitions and background scaling.
  * Secure credential storage utilizing SHA-256 password hashing.
  * Support for user roles (`admin`, `staff`) and mobile contact storage.

* **Database Migration & Seeding (`migrate_db.py`, `seed_categories.py`, `seed_products.py`)**:
  * Automated migration script creating all relational tables, foreign key constraints, and cascading rules.
  * Category and product seeders populated with realistic supplement catalog data and randomized starting inventory.

---

## Technology Stack

The application is built with the following technologies and libraries:

* **Programming Language**: Python 3.10+
* **Desktop GUI Framework**: PyQt6 (v6.7.1)
* **Database**: PostgreSQL
* **Database Driver**: `psycopg` / `psycopg2-binary` (v2.9.9)
* **Document / Invoice Generation**: ReportLab (v4.2.5)
* **Data Visualization**: Matplotlib (`FigureCanvasQTAgg`)
* **UI Design & Styling**: Qt Designer (`sidebar.ui`), Qt Resource Compiler (`resources_rc.py`), Qt Style Sheets (`style.qss`)
* **Supporting Utilities**: `openpyxl` (v3.1.5), `requests` (v2.32.3)

---

## Project Structure

```text
Stockease/
├── main.py                 # Primary application entry point & navigation controller
├── front_page.py           # Authentication UI (Login and Sign-up interface)
├── dashboard.py            # Generated PyQt6 UI class for the main application shell
├── database.py             # Database configuration, hashing, and auth queries
├── db_connect.py           # Direct database connection and authentication helper
├── inventory.py            # Inventory tracking and stock management module
├── product.py              # Product catalog and category operations module
├── Purchase_Order.py       # Supplier purchase order lifecycle management
├── salesorder.py           # Sales order processing and PDF invoice generation
├── return_refund.py        # Customer returns processing and stock restorer
├── graph.py                # Sales performance analytics and Matplotlib chart
├── migrate_db.py           # Database migration script creating application tables
├── seed_categories.py      # Seed script for initial product categories
├── seed_products.py        # Seed script for initial products and inventory levels
├── stockease_schema.sql    # Raw PostgreSQL schema definition with stock triggers
├── requirement.txt         # Project dependencies
├── style.qss               # Application Qt stylesheet
├── sidebar.ui              # Qt Designer layout for the navigation sidebar
├── resources_rc.py         # Compiled Qt resources for icons and embedded assets
├── muscle_base.png         # Application branding logo asset
├── backg.png               # Login window background artwork
└── icon/                   # UI navigation and button icons
```

---

## Installation

### Prerequisites

* Python 3.10 or higher installed on your system.
* PostgreSQL server installed, running, and accessible locally or remotely.

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Stockease
   ```

2. **Create and activate a virtual environment:**

   On macOS / Linux:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   On Windows:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirement.txt
   ```

---

## Database Setup

Stockease relies on PostgreSQL for persistent data storage.

### 1. Create the Database

Open your PostgreSQL client (such as `psql` or pgAdmin) and create a new database:

```sql
CREATE DATABASE stockease_db;
```

### 2. Configure Database Credentials

Database connection parameters are defined in `database.py`. Update the dictionary values to match your local PostgreSQL configuration:

```python
DB_CONFIG = {
    "dbname": "stockease_db",
    "user": "<your_postgres_username>",
    "password": "<your_postgres_password>",
    "host": "localhost",
    "port": "5432"
}
```

> **Note**: If using `db_connect.py` independently, ensure it imports `DB_CONFIG` from `database.py` or contains matching connection credentials.

### 3. Run Database Migrations

Initialize the required database schema by running the migration utility:

```bash
python migrate_db.py
```

This creates the necessary relational tables (`categories`, `products`, `inventory`, `sales_orders`, `invoices`, `purchase_orders`, `returns`, and `users`).

### 4. (Optional) Seed Sample Data

To populate the database with baseline categories, products, and initial stock quantities:

```bash
python seed_categories.py
python seed_products.py
```

---

## Running the Application

Stockease provides two execution options depending on whether authentication is required:

### Option 1: Direct Main Dashboard (Default)

To launch directly into the main application dashboard with full sidebar navigation:

```bash
python main.py
```

### Option 2: Authentication Screen

To launch the login and registration window first:

```bash
python front_page.py
```

Upon successful login or user registration, the authentication window opens the main dashboard view.

---

## Main Modules

| Module | Primary Responsibility |
|---|---|
| `main.py` | Orchestrates the primary `MainWindow`, initializes all view windows, binds sidebar navigation buttons, and switches pages in `QStackedWidget`. |
| `front_page.py` | Renders the login and registration screen with field animations, handles authentication, and transitions to `MainWindow`. |
| `product.py` | Manages the product catalog, category listings, adding new products, and deleting existing products. |
| `inventory.py` | Displays current stock counts, filters items by category, restocks quantities, and handles inventory item deletions. |
| `salesorder.py` | Handles sales order entry, validates stock availability, deducts inventory, records invoices, and exports PDF invoice files. |
| `Purchase_Order.py` | Creates purchase orders with suppliers, tracks execution state, and updates inventory stock upon fulfillment. |
| `return_refund.py` | Validates customer return requests against sales orders and restores returned stock back into active inventory. |
| `graph.py` | Embedded Matplotlib view generating interactive sales performance bar charts with revenue and order volume metrics. |
| `dashboard.py` | UI layout generated from Qt Designer defining the main window frame and navigation bar containers. |
| `database.py` / `db_connect.py` | Manages PostgreSQL connections, user authentication routines, and SHA-256 password hashing. |
| `migrate_db.py` | Executes table creation and schema definitions required by the application models. |
| `seed_categories.py` / `seed_products.py` | Seeds initial fitness supplement categories, sample products, and baseline inventory counts. |

---

## Development Notes

Stockease was developed as an academic and software engineering project focused on practical inventory tracking, transactional order flows, and desktop GUI engineering. The repository contains the application's source code, database migration and seed utilities, UI layout specifications, styling files, and graphic assets.
