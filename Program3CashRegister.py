#!/usr/bin/env python3
"""
Cash Register CLI with explicit Admin/Cashier modes
SkillsUSA State 2026

A command-line version of the cash register application with "admin" and "cashier" mode groups.
"""

import argparse
import sqlite3
import datetime
import sys


class CashRegisterDatabase:
    """Database for inventory and sales."""

    def __init__(self, db_path="cash_register.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.init_db()

    def init_db(self):
        """Create required tables if they do not exist."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                sku TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                unit_cost REAL NOT NULL,
                sale_price REAL NOT NULL,
                quantity_on_hand INTEGER NOT NULL DEFAULT 0
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sku TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price_per_item REAL NOT NULL,
                subtotal REAL NOT NULL,
                tax_amount REAL NOT NULL,
                total REAL NOT NULL
            )
        ''')
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def add_item(self, sku, description, unit_cost, sale_price, quantity):
        """Add or update an inventory item."""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO inventory
                (sku, description, unit_cost, sale_price, quantity_on_hand)
                VALUES (?, ?, ?, ?, ?)
            ''', (sku, description, float(unit_cost), float(sale_price), int(quantity)))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding item: {e}")
            return False

    def get_item(self, sku):
        """Retrieve a single inventory item by SKU."""
        self.cursor.execute(
            'SELECT sku, description, unit_cost, sale_price, quantity_on_hand FROM inventory WHERE sku = ?',
            (sku,)
        )
        return self.cursor.fetchone()

    def get_all_items(self):
        """Get all inventory items."""
        self.cursor.execute('SELECT sku, description, unit_cost, sale_price, quantity_on_hand FROM inventory ORDER BY sku')
        return self.cursor.fetchall()

    def update_quantity(self, sku, quantity_change):
        """Update inventory quantity for a SKU."""
        try:
            self.cursor.execute('''
                UPDATE inventory
                SET quantity_on_hand = quantity_on_hand + ?
                WHERE sku = ?
            ''', (quantity_change, sku))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating quantity: {e}")
            return False

    def record_sale(self, sku, quantity, price_per_item):
        """Record a completed sale."""
        try:
            subtotal = quantity * price_per_item
            tax_rate = 0.055
            tax_amount = subtotal * tax_rate
            total = subtotal + tax_amount
            self.cursor.execute('''
                INSERT INTO sales (sku, quantity, price_per_item, subtotal, tax_amount, total)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (sku, quantity, price_per_item, subtotal, tax_amount, total))
            self.conn.commit()
            return self.cursor.lastrowid, subtotal, tax_amount, total
        except Exception as e:
            print(f"Error recording sale: {e}")
            return None

    def get_daily_sales(self, date=None):
        """Return all sales for the given date."""
        if date is None:
            date = datetime.date.today().isoformat()
        self.cursor.execute('''
            SELECT s.transaction_id, s.date, s.sku, i.description, s.quantity,
                   s.price_per_item, s.subtotal, s.tax_amount, s.total
            FROM sales s
            JOIN inventory i ON s.sku = i.sku
            WHERE DATE(s.date) = ?
            ORDER BY s.date DESC
        ''', (date,))
        return self.cursor.fetchall()


def print_inventory(items):
    if not items:
        print("No items in inventory.")
        return
    print("\nCurrent Inventory")
    print("SKU     Description                 Cost     Price    Qty")
    print("-----   --------------------------   -----    -----    ---")
    for sku, desc, cost, price, qty in items:
        print(f"{sku:<7} {desc:<26} ${cost:>6.2f}  ${price:>6.2f}  {qty:>3}")


def print_sales(sales):
    if not sales:
        print("No sales found for that date.")
        return
    print("\nDaily Sales")
    print("TID  Date                     SKU    Item                 Qty  Price   Total")
    print("---  -----------------------  -----  --------------------  ---  ------  -------")
    for tid, date, sku, desc, qty, price, subtotal, tax, total in sales:
        print(f"{tid:<4} {date:<23} {sku:<5} {desc[:20]:<20} {qty:>3}  ${price:>6.2f}  ${total:>7.2f}")


def print_summary(items):
    #Calculate totals and profit
    total_items = len(items)
    total_cost = sum(cost * qty for _, _, cost, _, qty in items)
    total_value = sum(price * qty for _, _, _, price, qty in items)
    profit = total_value - total_cost
    print("\nInventory Summary")
    print(f"Total items: {total_items}")
    print(f"Total cost: ${total_cost:.2f}")
    print(f"Total value: ${total_value:.2f}")
    print(f"Projected gross profit: ${profit:.2f}")


def cli_add_item(db, args):
    if db.add_item(args.sku, args.description, args.unit_cost, args.sale_price, args.quantity):
        print(f"Item {args.sku} added/updated successfully.")
    else:
        sys.exit(1)


def cli_list_inventory(db, args):
    print_inventory(db.get_all_items())


def cli_show_summary(db, args):
    print_summary(db.get_all_items())


def cli_record_sale(db, args):
    #Validate SKU and quantity, then record sale and update inventory
    item = db.get_item(args.sku)
    if not item:
        print(f"Error: SKU {args.sku} not found.")
        sys.exit(1)
    sku, desc, cost, price, qty = item
    if args.quantity <= 0:
        print("Error: Quantity must be positive.")
        sys.exit(1)
    if qty < args.quantity:
        print(f"Error: Not enough stock ({qty} available).")
        sys.exit(1)
    sale = db.record_sale(args.sku, args.quantity, price)
    if sale:
        db.update_quantity(args.sku, -args.quantity)
        tid, subtotal, tax, total = sale
        print(f"Sale recorded. Transaction ID: {tid}")
        print(f"Subtotal: ${subtotal:.2f}, Tax: ${tax:.2f}, Total: ${total:.2f}")
    else:
        sys.exit(1)


def cli_daily_sales(db, args):
    print_sales(db.get_daily_sales(args.date))


def parse_args():
    #Add args
    parser = argparse.ArgumentParser(description="Cash Register CLI with explicit admin/cashier modes")
    parser.add_argument("--db", default="cash_register.db", help="SQLite database file")

    subparsers = parser.add_subparsers(dest="mode", required=True)

    admin_parser = subparsers.add_parser("admin", help="Admin mode for inventory and reporting")
    admin_subparsers = admin_parser.add_subparsers(dest="command", required=True)

    add_parser = admin_subparsers.add_parser("add", help="Add or update an inventory item")
    add_parser.add_argument("--sku", required=True, help="Item SKU")
    add_parser.add_argument("--description", required=True, help="Item description")
    add_parser.add_argument("--unit-cost", type=float, required=True, help="Item cost")
    add_parser.add_argument("--sale-price", type=float, required=True, help="Sale price")
    add_parser.add_argument("--quantity", type=int, default=0, help="Quantity on hand")
    add_parser.set_defaults(func=cli_add_item)

    admin_subparsers.add_parser("list", help="List inventory items").set_defaults(func=cli_list_inventory)
    admin_subparsers.add_parser("summary", help="Show inventory summary").set_defaults(func=cli_show_summary)

    report_parser = admin_subparsers.add_parser("report", help="Show sales for a date")
    report_parser.add_argument("--date", default=datetime.date.today().isoformat(), help="Date for sales report (YYYY-MM-DD)")
    report_parser.set_defaults(func=cli_daily_sales)

    cashier_parser = subparsers.add_parser("cashier", help="Cashier mode for recording sales")
    cashier_subparsers = cashier_parser.add_subparsers(dest="command", required=True)

    sale_parser = cashier_subparsers.add_parser("sale", help="Record a sale transaction")
    sale_parser.add_argument("--sku", required=True, help="Item SKU")
    sale_parser.add_argument("--quantity", type=int, default=1, help="Quantity sold")
    sale_parser.set_defaults(func=cli_record_sale)

    return parser.parse_args()


def main():
    args = parse_args()
    db = CashRegisterDatabase(args.db)
    try:
        args.func(db, args)
    finally:
        db.close()


if __name__ == "__main__":
    main()
