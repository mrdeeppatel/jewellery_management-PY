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
            
            btn_pdf = QPushButton("📄 PDF")
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
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        from datetime import datetime

        voucher = bill["voucher"]
        date_str = bill["date"].split(" ")[0]
        default_name = f"Bill_{voucher}_{date_str}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Bill PDF", default_name, "PDF Files (*.pdf)")
        
        if not file_path:
            return
            
        try:
            doc = SimpleDocTemplate(file_path, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=15*mm, rightMargin=15*mm)
            elements = []
            styles = getSampleStyleSheet()
            black = colors.black

            title_style = ParagraphStyle('BillTitle', parent=styles['Title'], fontSize=18, leading=22, alignment=TA_CENTER, textColor=black, fontName='Helvetica-Bold', spaceAfter=2)
            elements.append(Paragraph("JEWELLERY BILL", title_style))
            elements.append(Spacer(1, 6*mm))

            info_data = [
                ["Voucher", voucher, "Date", date_str],
                ["Party", bill["customer_name"], "Generated", datetime.now().strftime('%d-%m-%Y %I:%M %p')],
            ]
            info_table = Table(info_data, colWidths=[doc.width*0.15, doc.width*0.35, doc.width*0.15, doc.width*0.35])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'), ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 10), ('TEXTCOLOR', (0,0), (-1,-1), black),
                ('GRID', (0,0), (-1,-1), 0.75, black), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('LEFTPADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 8*mm))

            header_row = ["#", "Tag / Design", "Item Name", "Net Wt (g)", "Touch %", "Wastage %", "Fine (g)"]
            table_data = [header_row]
            total_net_wt = 0.0

            for idx, item in enumerate(bill["items"]):
                tag = item.get("tag", "")
                name = item.get("name", "")
                net_wt = item.get("net_wt", 0)
                touch = item.get("touch", 0)
                wastage = item.get("wastage", 0)
                fine = item.get("fine", 0)
                total_net_wt += float(net_wt)
                table_data.append([str(idx+1), tag, name, f"{net_wt:.3f}", f"{touch:.2f}", f"{wastage:.2f}", f"{fine:.3f}"])

            table_data.append(["", "", "TOTAL", f"{total_net_wt:.3f}", "", "", f"{bill['total_fine']:.3f}"])
            col_widths = [25, 70, 90, 60, 55, 60, 60]
            items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            items_table.setStyle(TableStyle([
                ('TEXTCOLOR', (0,0), (-1,-1), black), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 10), ('TOPPADDING', (0,0), (-1,0), 8), ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('FONTSIZE', (0,1), (-1,-1), 9), ('TOPPADDING', (0,1), (-1,-1), 5), ('BOTTOMPADDING', (0,1), (-1,-1), 5),
                ('ALIGN', (0,0), (0,-1), 'CENTER'), ('ALIGN', (3,0), (-1,-1), 'RIGHT'),
                ('GRID', (0,0), (-1,-1), 0.75, black), ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ]))
            elements.append(items_table)
            elements.append(Spacer(1, 8*mm))

            summary_data = [
                ["Bill Summary", ""],
                ["Total Fine", f"{bill['total_fine']:.3f} g"],
                ["99.50 Fine", f"{bill['fine_9950']:.3f} g"],
                ["Rate Cut (per 10 gm)", f"Rs. {bill['rate_cut']:.2f}"],
                ["Total Amount", f"₹ {bill['total_amount']:,.2f}"],
            ]
            summary_table = Table(summary_data, colWidths=[doc.width*0.5, doc.width*0.5])
            summary_table.setStyle(TableStyle([
                ('TEXTCOLOR', (0,0), (-1,-1), black), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 11), ('SPAN', (0,0), (-1,0)), ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'), ('FONTSIZE', (0,1), (-1,-1), 10),
                ('ALIGN', (1,1), (1,-1), 'RIGHT'), ('GRID', (0,0), (-1,-1), 0.75, black),
                ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), ('FONTSIZE', (0,-1), (-1,-1), 11),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 10*mm))
            
            ts_style = ParagraphStyle('Timestamp', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=black, spaceBefore=10)
            elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%d-%m-%Y %I:%M:%S %p')}", ts_style))

            doc.build(elements)
            QMessageBox.information(self, "Success", f"PDF Generated successfully!\n{file_path}")
            os.startfile(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF.\n{str(e)}")
