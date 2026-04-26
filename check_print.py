import random
import logging
import socket
from datetime import datetime
import os

from reportlab.lib.pagesizes import A6
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

import win32print
import win32api

# -----------------------------
# 🔹 Logging Setup
# -----------------------------
logging.basicConfig(
    filename="printer_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -----------------------------
# 🔹 Generate Random Gold Data
# -----------------------------
def generate_gold_data():
    items = ["Ring", "Necklace", "Bracelet", "Chain", "Pendant"]

    item = random.choice(items)
    weight = round(random.uniform(2.0, 20.0), 2)
    rate_per_gram = random.randint(5000, 7000)

    gold_price = weight * rate_per_gram
    making_charge = gold_price * random.uniform(0.05, 0.15)

    subtotal = gold_price + making_charge
    gst = subtotal * 0.03
    total = subtotal + gst

    return {
        "item": item,
        "weight": weight,
        "rate": rate_per_gram,
        "gold_price": round(gold_price, 2),
        "making_charge": round(making_charge, 2),
        "gst": round(gst, 2),
        "total": round(total, 2)
    }

# -----------------------------
# 🔹 Generate A6 PDF
# -----------------------------
def create_pdf(data, filename="invoice_a6.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A6)
    styles = getSampleStyleSheet()

    elements = []

    title = Paragraph("<b>Gold Invoice (A6)</b>", styles["Title"])
    elements.append(title)

    table_data = [
        ["Item", data["item"]],
        ["Weight (g)", data["weight"]],
        ["Rate/g", data["rate"]],
        ["Gold Price", data["gold_price"]],
        ["Making Charge", data["making_charge"]],
        ["GST (3%)", data["gst"]],
        ["Total", data["total"]],
    ]

    table = Table(table_data)
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
    ]))

    elements.append(table)

    doc.build(elements)
    print("✅ PDF Generated:", filename)
    logging.info(f"PDF generated: {filename}")

    return os.path.abspath(filename)

# -----------------------------
# 🔹 Detect Printers
# -----------------------------
def detect_printers():
    printers = win32print.EnumPrinters(
        win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    )

    printer_list = []

    for p in printers:
        name = p[2]
        try:
            handle = win32print.OpenPrinter(name)
            info = win32print.GetPrinter(handle, 2)

            printer_data = {
                "name": name,
                "status": info["Status"],
                "driver": info["pDriverName"],
                "port": info["pPortName"]
            }

            printer_list.append(printer_data)

            # Logging
            logging.info(f"Printer Found: {printer_data}")

            win32print.ClosePrinter(handle)

        except Exception as e:
            logging.error(f"Error reading printer {name}: {e}")

    return printer_list

# -----------------------------
# 🔹 Select Best Printer
# -----------------------------
def select_printer(printers):
    for p in printers:
        if "EPSON" in p["name"].upper():
            logging.info(f"Selected Epson Printer: {p['name']}")
            return p["name"]

    default = win32print.GetDefaultPrinter()
    logging.info(f"No Epson found. Using default: {default}")
    return default

# -----------------------------
# 🔹 Print PDF
# -----------------------------
def print_pdf(file_path, printer_name):
    try:
        win32print.SetDefaultPrinter(printer_name)

        win32api.ShellExecute(
            0,
            "print",
            file_path,
            None,
            ".",
            0
        )

        print(f"🖨 Printing to: {printer_name}")
        logging.info(f"Printing {file_path} to {printer_name}")

    except Exception as e:
        logging.error(f"Print error: {e}")
        print("❌ Print failed:", e)

# -----------------------------
# 🔹 Network Info Logging
# -----------------------------
def log_network_info():
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)

        logging.info(f"Hostname: {hostname}")
        logging.info(f"IP Address: {ip}")

    except Exception as e:
        logging.error(f"Network error: {e}")

# -----------------------------
# 🔹 MAIN FLOW
# -----------------------------
if __name__ == "__main__":
    print("🔍 Detecting printers...")

    printers = detect_printers()

    for p in printers:
        print(p)

    log_network_info()

    print("\n📄 Generating PDF...")
    data = generate_gold_data()
    pdf_file = create_pdf(data)

    print("\n🎯 Selecting printer...")
    selected_printer = select_printer(printers)

    print("\n🖨 Printing...")
    print_pdf(pdf_file, selected_printer)

    print("\n✅ Done!")
    print("📄 Check 'printer_log.txt' for logs")