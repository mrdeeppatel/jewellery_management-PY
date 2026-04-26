import random
import logging
import socket
import os
import json
from datetime import datetime

from reportlab.lib.pagesizes import A6
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

import win32print
import win32api

# -----------------------------
# 🔹 Setup & Constants
# -----------------------------
LOG_FILE = "printer_system.log"
REPORT_FILE = "dev_env_report.json"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -----------------------------
# 🔹 Data & PDF Logic
# -----------------------------
def generate_gold_data():
    items = ["Ring", "Necklace", "Bracelet", "Chain", "Pendant"]
    weight = round(random.uniform(2.0, 20.0), 2)
    rate = random.randint(5000, 7000)
    gold_price = round(weight * rate, 2)
    making = round(gold_price * random.uniform(0.05, 0.15), 2)
    gst = round((gold_price + making) * 0.03, 2)
    
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "item": random.choice(items),
        "weight": weight,
        "rate": rate,
        "gold_price": gold_price,
        "making_charge": making,
        "gst": gst,
        "total": round(gold_price + making + gst, 2)
    }

def create_pdf(data, filename="invoice_a6.pdf"):
    path = os.path.abspath(filename)
    doc = SimpleDocTemplate(path, pagesize=A6)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>GOLD INVOICE</b>", styles["Title"]))
    
    table_data = [[k.replace("_", " ").title(), v] for k, v in data.items()]
    table = Table(table_data)
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (0,-1), colors.whitesmoke),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
    ]))
    
    elements.append(table)
    doc.build(elements)
    logging.info(f"PDF Created at: {path}")
    return path

# -----------------------------
# 🔹 Hardware Discovery & Reporting
# -----------------------------
def get_system_context():
    """Generates a diagnostic report for future development."""
    printers = []
    try:
        raw_printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        for p in raw_printers:
            h = win32print.OpenPrinter(p[2])
            info = win32print.GetPrinter(h, 2)
            printers.append({
                "name": p[2],
                "driver": info['pDriverName'],
                "port": info['pPortName'],
                "status": info['Status']
            })
            win32print.ClosePrinter(h)
    except Exception as e:
        logging.error(f"Discovery Error: {e}")

    report = {
        "scan_time": datetime.now().isoformat(),
        "machine": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname()),
        "os": os.name,
        "found_printers": printers,
        "default_printer": win32print.GetDefaultPrinter()
    }
    
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=4)
    
    return report

# -----------------------------
# 🔹 Printing Logic
# -----------------------------
def execute_print(file_path, printer_name):
    """Prints if it's a physical printer; saves if virtual."""
    
    # List of virtual printers that shouldn't be 'force-printed'
    virtual_keywords = ["PDF", "ONENOTE", "FAX", "DOCUMENT WRITER"]
    is_virtual = any(key in printer_name.upper() for key in virtual_keywords)

    if is_virtual:
        print(f"⚠️ '{printer_name}' is a virtual printer. Skipping physical print to avoid UI popups.")
        print(f"📁 PDF is available at: {file_path}")
        logging.info(f"Skipped printing: {printer_name} is virtual.")
        return False

    try:
        print(f"🖨 Sending to: {printer_name}...")
        # Using 'printto' avoids changing system defaults
        win32api.ShellExecute(0, "printto", file_path, f'"{printer_name}"', ".", 0)
        logging.info(f"Print job sent to {printer_name}")
        return True
    except Exception as e:
        logging.error(f"Hardware Error: {e}")
        return False

# -----------------------------
# 🔹 Main Logic
# -----------------------------
if __name__ == "__main__":
    print("--- 🔍 SYSTEM SCAN ---")
    sys_report = get_system_context()
    print(f"Hostname: {sys_report['machine']} | Printers Found: {len(sys_report['found_printers'])}")

    # 1. Generate PDF
    data = generate_gold_data()
    pdf_path = create_pdf(data)

    # 2. Printer Selection Logic
    target_printer = None
    printers = sys_report['found_printers']
    
    # Priority: 1. Epson, 2. Any physical printer, 3. Default
    epson = next((p['name'] for p in printers if "EPSON" in p['name'].upper()), None)
    
    if epson:
        target_printer = epson
        print(f"🎯 Target: Epson found ({epson})")
    else:
        target_printer = sys_report['default_printer']
        print(f"ℹ️ Target: No Epson. Using default ({target_printer})")

    # 3. Final Print Option
    choice = input(f"\nProceed to print to '{target_printer}'? (y/n): ").lower()
    if choice == 'y':
        execute_print(pdf_path, target_printer)
    else:
        print("❌ Printing cancelled by user.")

    print(f"\n✅ Session Complete. Logs: {LOG_FILE} | Report: {REPORT_FILE}")