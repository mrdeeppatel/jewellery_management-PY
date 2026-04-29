from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import sys
from models.database import get_db, Bill

class BillsLoaderThread(QThread):
    data_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            db = next(get_db())
            bills = db.query(Bill).order_by(Bill.date.desc()).all()
            result = []
            for b in bills:
                items_data = []
                for i in b.items:
                    items_data.append({
                        "tag": getattr(i, 'tag', '') or '',
                        "name": getattr(i, 'name', '') or '',
                        "net_wt": getattr(i, 'net_wt', 0) or 0,
                        "touch": getattr(i, 'touch', 0) or 0,
                        "wastage": getattr(i, 'wastage', 0) or 0,
                        "fine": getattr(i, 'fine', 0) or 0
                    })
                
                result.append({
                    "id": b.id,
                    "voucher": getattr(b, 'voucher', 'N/A') or 'N/A',
                    "customer_name": b.customer_name,
                    "customer_phone": b.customer_phone or "N/A",
                    "date": b.date.strftime("%d-%m-%Y %I:%M %p"),
                    "total_amount": b.total_amount,
                    "total_fine": getattr(b, 'total_fine', 0.0) or 0.0,
                    "fine_9950": getattr(b, 'fine_9950', 0.0) or 0.0,
                    "rate_cut": getattr(b, 'rate_cut', 0.0) or 0.0,
                    "items": items_data
                })
            db.close()
            self.data_loaded.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))

class AllBills(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("All Bills")
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        title = QLabel("🧾 All Bills History")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #2c3e50;")
        
        self.btn_delete_selected = QPushButton("🗑 Delete Selected")
        self.btn_delete_selected.setCursor(Qt.PointingHandCursor)
        self.btn_delete_selected.setStyleSheet("""
            QPushButton { background-color: #f39c12; color: white; border-radius: 8px; padding: 8px 15px; font-size: 16px; font-weight: bold; }
            QPushButton:hover { background-color: #e67e22; }
        """)
        self.btn_delete_selected.clicked.connect(self.delete_selected_bills)

        self.btn_delete_all = QPushButton("⚠️ Delete All")
        self.btn_delete_all.setCursor(Qt.PointingHandCursor)
        self.btn_delete_all.setStyleSheet("""
            QPushButton { background-color: #E03131; color: white; border-radius: 8px; padding: 8px 15px; font-size: 16px; font-weight: bold; }
            QPushButton:hover { background-color: #c92a2a; }
        """)
        self.btn_delete_all.clicked.connect(self.delete_all_bills)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setStyleSheet("""
            QPushButton { background-color: #0d6efd; color: white; border-radius: 8px; padding: 8px 15px; font-size: 16px; font-weight: bold; }
            QPushButton:hover { background-color: #0b5ed7; }
        """)
        self.refresh_btn.clicked.connect(self.refresh_data)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_delete_selected)
        header_layout.addWidget(self.btn_delete_all)
        header_layout.addWidget(self.refresh_btn)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["Select", "ID", "Voucher", "Customer", "Date", "Items", "Total Fine", "Amount (₹)", "Action"])
        
        self.table.setMinimumHeight(400)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(55)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setDefaultAlignment(Qt.AlignCenter)

        self.table.setStyleSheet("""
        QTableWidget { background-color: #ffffff; border: 1px solid #dcdcdc; border-radius: 12px; font-size: 14px; }
        QHeaderView::section { background-color: #f5f6fa; border: none; border-bottom: 2px solid #e0e0e0; font-weight: bold; font-size: 15px; padding: 10px; }
        QTableWidget::item { padding: 5px; }
        QTableWidget::item:selected { background-color: #007bff; color: white; }
        QTableWidget::item:hover { background-color: #f0f4ff; }
        """)
        
        card = QFrame()
        card.setStyleSheet("QFrame { background-color: #ffffff; border-radius: 15px; border: 1px solid #e0e0e0; }")
        card_layout = QVBoxLayout()
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        card_layout.addLayout(header_layout)
        card_layout.addWidget(self.table)
        card.setLayout(card_layout)
        
        main_layout.addWidget(card)
        self.setLayout(main_layout)
        
        self.loading_overlay = QLabel("⏳ Fetching bills...", self)
        self.loading_overlay.setStyleSheet("background-color: rgba(255, 255, 255, 220); font-size: 26px; font-weight: bold; color: #333;")
        self.loading_overlay.setAlignment(Qt.AlignCenter)
        self.loading_overlay.hide()
        
        self.data_thread = BillsLoaderThread()
        self.data_thread.data_loaded.connect(self.update_ui)
        self.data_thread.error_occurred.connect(self.handle_error)

    def resizeEvent(self, event):
        self.loading_overlay.resize(self.size())
        super().resizeEvent(event)

    def showEvent(self, event):
        self.refresh_data()
        super().showEvent(event)

    def refresh_data(self):
        self.loading_overlay.show()
        if not self.data_thread.isRunning():
            self.data_thread.start()

    def update_ui(self, bills):
        self.table.setRowCount(len(bills))
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)

        for row, bill in enumerate(bills):
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setContentsMargins(0,0,0,0)
            chk = QCheckBox()
            chk.setStyleSheet("margin-left: 10px; margin-right: 10px;")
            chk_layout.addWidget(chk, alignment=Qt.AlignCenter)
            chk_widget.setProperty("bill_id", bill["id"])
            self.table.setCellWidget(row, 0, chk_widget)

            id_item = QTableWidgetItem(f"#{bill['id']}")
            id_item.setTextAlignment(Qt.AlignCenter)
            id_item.setFont(QFont("Segoe UI", 12, QFont.Bold))
            id_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 1, id_item)

            voucher_item = QTableWidgetItem(bill["voucher"])
            voucher_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, voucher_item)

            name_item = QTableWidgetItem(bill["customer_name"])
            name_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, name_item)

            date_item = QTableWidgetItem(bill["date"])
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, date_item)

            items_item = QTableWidgetItem(f"{len(bill['items'])} items")
            items_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, items_item)

            fine_item = QTableWidgetItem(f"{bill['total_fine']:.3f} g")
            fine_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, fine_item)

            total_item = QTableWidgetItem(f"₹{bill['total_amount']:,.2f}")
            total_item.setTextAlignment(Qt.AlignCenter)
            total_item.setFont(QFont("Segoe UI", 12, QFont.Bold))
            total_item.setForeground(QColor("#00a86b"))
            self.table.setItem(row, 7, total_item)
            
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0,0,0,0)
            btn_layout.setSpacing(10)
            
            btn_pdf = QPushButton("🖨 Print")
            btn_pdf.setStyleSheet("background-color: #2B8A3E; color: white; border-radius: 4px; padding: 4px 8px; font-weight: bold;")
            btn_pdf.setCursor(Qt.PointingHandCursor)
            btn_pdf.clicked.connect(lambda checked, b=bill: self.generate_pdf_for_bill(b))
            
            btn_delete = QPushButton("🗑 Delete")
            btn_delete.setStyleSheet("background-color: #E03131; color: white; border-radius: 4px; padding: 4px 8px; font-weight: bold;")
            btn_delete.setCursor(Qt.PointingHandCursor)
            btn_delete.clicked.connect(lambda checked, b_id=bill['id']: self.delete_bill(b_id))
            
            btn_layout.addWidget(btn_pdf)
            btn_layout.addWidget(btn_delete)
            btn_layout.setAlignment(Qt.AlignCenter)
            
            self.table.setCellWidget(row, 8, btn_widget)
            
        self.loading_overlay.hide()

    def handle_error(self, err_msg):
        self.loading_overlay.hide()
        QMessageBox.critical(self, "Database Error", f"Failed to load bills data.\nPlease check your connection and try again.\n\nDetails: {err_msg}")

    def delete_bill(self, bill_id):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete Bill #{bill_id}? This action cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._execute_delete([bill_id])

    def delete_selected_bills(self):
        selected_ids = []
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                chk = widget.findChild(QCheckBox)
                if chk and chk.isChecked():
                    selected_ids.append(widget.property("bill_id"))
        
        if not selected_ids:
            QMessageBox.warning(self, "No Selection", "Please select at least one bill to delete.")
            return

        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete {len(selected_ids)} selected bills? This action cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._execute_delete(selected_ids)

    def delete_all_bills(self):
        reply = QMessageBox.question(self, "Confirm Delete All", 
                                     "⚠️ WARNING: Are you sure you want to delete ALL bills? This action cannot be undone and will clear the entire billing history.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            from models.database import get_db, Bill, BillItem
            try:
                db = next(get_db())
                db.query(BillItem).delete()
                db.query(Bill).delete()
                db.commit()
                QMessageBox.information(self, "Success", "All bills have been deleted successfully.")
                self.refresh_data()
                db.close()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete all bills: {str(e)}")

    def _execute_delete(self, bill_ids):
        from models.database import get_db, Bill, BillItem
        try:
            db = next(get_db())
            db.query(BillItem).filter(BillItem.bill_id.in_(bill_ids)).delete(synchronize_session=False)
            db.query(Bill).filter(Bill.id.in_(bill_ids)).delete(synchronize_session=False)
            db.commit()
            msg = f"Bill #{bill_ids[0]} deleted successfully." if len(bill_ids) == 1 else f"{len(bill_ids)} bills deleted successfully."
            QMessageBox.information(self, "Success", msg)
            self.refresh_data()
            db.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete bills: {str(e)}")

    def generate_pdf_for_bill(self, bill):
        import os
        import tempfile
        import webbrowser
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.pagesizes import A5
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from datetime import datetime
        import math as _math
        from collections import OrderedDict

        voucher = bill["voucher"]
        date_str = bill["date"].split(" ")[0]
        
        # Save to temp directory automatically for printing
        default_name = f"{voucher}_{date_str}_{bill['customer_name']}.pdf"
        file_path = os.path.join(tempfile.gettempdir(), default_name)
            
        try:
            # ── Register Gujarati-capable font ──
            font_path = r'C:\Windows\Fonts\shruti.ttf'
            font_bold_path = r'C:\Windows\Fonts\shrutib.ttf'
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Shruti', font_path))
            if os.path.exists(font_bold_path):
                pdfmetrics.registerFont(TTFont('ShrutiBold', font_bold_path))

            guj_font = 'Shruti' if os.path.exists(font_path) else 'Helvetica'
            guj_bold = 'ShrutiBold' if os.path.exists(font_bold_path) else 'Helvetica-Bold'

            page_w, page_h = A5  # 148 x 210 mm

            doc = SimpleDocTemplate(
                file_path, pagesize=(page_w, page_h),
                topMargin=8*mm, bottomMargin=8*mm,
                leftMargin=6*mm, rightMargin=6*mm
            )
            usable_w = page_w - 12*mm
            elements = []
            black = colors.black

            # ── Top Header: Time / Date / Slip ──
            now = datetime.now()
            time_str  = now.strftime('%I:%M %p')
            date_str_pdf = now.strftime('%d-%m-%Y')
            header_data = [[
                f"Time: {time_str}",
                f"Date: {date_str_pdf}",
                f"Slip: {voucher}"
            ]]
            ht = Table(header_data, colWidths=[usable_w*0.35, usable_w*0.35, usable_w*0.30])
            ht.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), guj_bold),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('TEXTCOLOR', (0,0), (-1,-1), black),
                ('ALIGN', (0,0), (0,0), 'LEFT'),
                ('ALIGN', (1,0), (1,0), 'CENTER'),
                ('ALIGN', (2,0), (2,0), 'RIGHT'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            elements.append(ht)

            # Party name
            party = bill["customer_name"]
            if party and party != "Walk-in Customer":
                p_data = [[f"Party: {party}"]]
                pt = Table(p_data, colWidths=[usable_w])
                pt.setStyle(TableStyle([
                    ('FONTNAME', (0,0), (-1,-1), guj_bold),
                    ('FONTSIZE', (0,0), (-1,-1), 9),
                    ('TEXTCOLOR', (0,0), (-1,-1), black),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ]))
                elements.append(pt)

            elements.append(Spacer(1, 3*mm))

            # ── Gujarati Header Row ──
            headers = [
                "\u0ab5\u0abf\u0a97\u0aa4",       # વિગત
                "\u0a97\u0acd\u0ab0\u0acb\u0ab8",  # ગ્રોસ
                "\u0ab2\u0ac7\u0ab8",               # લેસ
                "\u0ab5\u0a9c\u0aa8",               # વજન
                "\u0a9f\u0a9a",                     # ટચ
                "\u0aab\u0abe\u0a88\u0aa8",         # ફાઈન
                "\u0aad\u0abe\u0ab5",               # ભાવ
                "\u0ab0\u0ac2\u0aaa\u0abf\u0aaf\u0abe"  # રૂપિયા
            ]

            # ── Collect & group rows by (vigat, touch) ──────────────────────────
            rate_val = float(bill.get("rate_cut", 0.0) or 0.0)
            groups = OrderedDict()

            for item in bill["items"]:
                tag = item.get("tag", "") or ""
                name = item.get("name", "") or ""
                net_wt = float(item.get("net_wt", 0.0) or 0.0)
                touch = float(item.get("touch", 0.0) or 0.0)
                wastage = float(item.get("wastage", 0.0) or 0.0)
                fine = float(item.get("fine", 0.0) or 0.0)

                vigat = tag if tag else name
                key   = (vigat, touch)

                gross = net_wt
                less  = 0.0

                if key not in groups:
                    groups[key] = {"vigat": vigat, "touch": touch,
                                   "gross": 0.0, "less": 0.0,
                                   "weight": 0.0, "fine": 0.0}
                groups[key]["gross"]  += gross
                groups[key]["less"]   += less
                groups[key]["weight"] += gross - less   # net weight
                groups[key]["fine"]   += fine

            # ── Build PDF table rows from groups ─────────────────────────────────
            table_data = [headers]
            total_gross     = 0.0
            total_less      = 0.0
            total_weight    = 0.0
            total_fine_val  = 0.0

            for g in groups.values():
                total_gross    += g["gross"]
                total_less     += g["less"]
                total_weight   += g["weight"]
                total_fine_val += g["fine"]

                table_data.append([
                    g["vigat"],
                    f"{g['gross']:.3f}",
                    f"{g['less']:.3f}",
                    f"{g['weight']:.3f}",
                    f"{g['touch']:.2f}",
                    f"{g['fine']:.3f}",
                    "",    # rate
                    "",    # amount
                ])

            # ── Totals row ────────────────────────────
            table_data.append([
                "Total",
                f"{total_gross:.3f}",
                f"{total_less:.3f}",
                f"{total_weight:.3f}",
                "",
                f"{total_fine_val:.3f}",
                "",
                "",
            ])

            # ── Rate / Ratt row ─────────────────
            if rate_val > 0:
                _raw = (total_fine_val * rate_val) / 10.0
                if _raw % 1 == 0:
                    final_amount = _raw
                else:
                    final_amount = _math.ceil(_raw * 100) / 100
            else:
                final_amount = 0.0

            def _fmt_amount(v):
                if v % 1 == 0:
                    return str(int(v))
                return f"{v:.2f}"

            ratt_row = [
                "Ratt",
                "",
                "",
                "",
                "",
                f"{total_fine_val:.3f}",
                f"{rate_val:.0f}" if rate_val > 0 else "",
                _fmt_amount(final_amount) if rate_val > 0 else "",
            ]
            table_data.append(ratt_row)

            # ── Final Total row ──────────────────────────────────────────────────
            table_data.append([
                "Total",
                "",
                "",
                "",
                "",
                "",
                "",
                _fmt_amount(final_amount) if rate_val > 0 else "",
            ])

            cw = [usable_w*0.14, usable_w*0.12, usable_w*0.10, usable_w*0.12,
                  usable_w*0.09, usable_w*0.13, usable_w*0.12, usable_w*0.18]
            items_table = Table(table_data, colWidths=cw, repeatRows=1)

            num_rows = len(table_data)
            totals_idx     = num_rows - 3
            ratt_idx       = num_rows - 2
            final_tot_idx  = num_rows - 1

            items_table.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,0), guj_bold),
                ('FONTSIZE', (0,0), (-1,0), 8),
                ('FONTNAME', (0,1), (-1,-1), guj_font),
                ('FONTSIZE', (0,1), (-1,-1), 7.5),
                ('TEXTCOLOR', (0,0), (-1,-1), black),
                ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
                ('ALIGN', (0,0), (0,-1), 'LEFT'),
                ('GRID', (0,0), (-1,-1), 0.6, black),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('LEFTPADDING', (0,0), (-1,-1), 3),
                ('RIGHTPADDING', (0,0), (-1,-1), 3),

                # Totals row styling
                ('LINEABOVE', (0, totals_idx), (-1, totals_idx), 1, black),
                ('FONTNAME', (0, totals_idx), (-1, totals_idx), guj_bold),
                ('FONTSIZE', (0, totals_idx), (-1, totals_idx), 8),

                # Ratt row styling
                ('LINEABOVE', (0, ratt_idx), (-1, ratt_idx), 1, black),
                ('FONTNAME', (0, ratt_idx), (-1, ratt_idx), guj_bold),
                ('FONTSIZE', (0, ratt_idx), (-1, ratt_idx), 8),

                # Final Total row styling
                ('LINEABOVE', (0, final_tot_idx), (-1, final_tot_idx), 1, black),
                ('FONTNAME', (0, final_tot_idx), (-1, final_tot_idx), guj_bold),
                ('FONTSIZE', (0, final_tot_idx), (-1, final_tot_idx), 9),
            ]))
            elements.append(items_table)
            
            elements.append(Spacer(1, 4*mm))

            # Footer
            footer_data = [
                [f"Qty: {len(groups)}", f"Fine: {total_fine_val:.3f}"]
            ]
            footer_table = Table(footer_data, colWidths=[usable_w*0.5, usable_w*0.5])
            footer_table.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), guj_bold),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('TEXTCOLOR', (0,0), (-1,-1), black),
                ('ALIGN', (0,0), (0,0), 'LEFT'),
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ]))
            elements.append(footer_table)

            doc.build(elements)
            webbrowser.open(f"file:///{os.path.realpath(file_path).replace(chr(92), '/')}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF.\n{str(e)}")
