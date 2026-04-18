import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QDateEdit,
    QApplication, QGraphicsDropShadowEffect, QSizePolicy, QAbstractItemView,
    QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


class ItemBillingPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        self.setWindowTitle("Item Billing Panel")
        self.setStyleSheet("""
            QWidget {
                background-color: #F8F9FA;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 15px;
                color: #343A40;
            }
            QLineEdit, QDateEdit {
                padding: 8px 12px;
                border: 1px solid #CED4DA;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus, QDateEdit:focus {
                border: 2px solid #4DABF7;
                outline: none;
            }
            QPushButton {
                background-color: #339AF0;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #228BE6;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #DEE2E6;
                border-radius: 8px;
                gridline-color: #E9ECEF;
            }
            QHeaderView::section {
                background-color: #F1F3F5;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #DEE2E6;
                font-weight: bold;
                color: #495057;
            }
            #cardFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #E9ECEF;
            }
            #amountLabel {
                font-size: 32px;
                font-weight: bold;
                color: #2B8A3E;
            }
            #grandTotalLabel {
                font-size: 24px;
                font-weight: bold;
                color: #E03131;
                padding: 15px;
                background-color: #FFF5F5;
                border-radius: 8px;
                border: 2px dashed #FFA8A8;
            }
            .panelLabel {
                font-size: 16px;
                color: #495057;
            }
            .panelValue {
                font-size: 18px;
                font-weight: bold;
                color: #212529;
            }
            .headerLabel {
                font-size: 20px;
                font-weight: bold;
                color: #212529;
                margin-bottom: 10px;
            }
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # =========================================================
        # LEFT SIDE
        # =========================================================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(15)

        # 1. Top Header
        top_header_layout = QHBoxLayout()
        top_header_layout.setSpacing(15)

        self.voucher_input = QLineEdit()
        self.voucher_input.setPlaceholderText("Voucher ID")

        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)

        self.party_input = QLineEdit()
        self.party_input.setPlaceholderText("Party Name")

        top_header_layout.addWidget(QLabel("Voucher:"))
        top_header_layout.addWidget(self.voucher_input)
        top_header_layout.addWidget(QLabel("Date:"))
        top_header_layout.addWidget(self.date_input)
        top_header_layout.addWidget(QLabel("Party:"))
        top_header_layout.addWidget(self.party_input)
        left_layout.addLayout(top_header_layout)

        # 2. Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["#", "Item Name", "Rate (₹)", "Total Pcs", "Amount (₹)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        left_layout.addWidget(self.table)

        # Table Controls
        table_controls_layout = QHBoxLayout()
        self.btn_generate_pdf = QPushButton("📄 Generate PDF Bill")
        self.btn_generate_pdf.setStyleSheet("background-color: #2B8A3E; color: white; padding: 6px 14px; font-size: 13px; font-weight: bold; border-radius: 4px;")
        self.btn_remove = QPushButton("🗑 Delete Selected")
        self.btn_remove.setStyleSheet("background-color: #FA5252; color: white; padding: 6px 12px; font-size: 13px; font-weight: bold; border-radius: 4px;")
        table_controls_layout.addWidget(self.btn_generate_pdf)
        table_controls_layout.addStretch()
        table_controls_layout.addWidget(self.btn_remove)
        left_layout.addLayout(table_controls_layout)

        # 3. Quick Entry Row
        qe_title = QLabel("Quick Entry:")
        qe_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #495057;")
        left_layout.addWidget(qe_title)

        quick_entry_layout = QHBoxLayout()
        quick_entry_layout.setSpacing(10)

        def create_qe_vbox(label_text, widget):
            vbox = QVBoxLayout()
            vbox.setSpacing(4)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 13px; color: #6C757D;")
            vbox.addWidget(lbl)
            vbox.addWidget(widget)
            return vbox

        self.qe_item_name = QLineEdit()
        self.qe_item_name.setPlaceholderText("Item Name")

        self.qe_rate = QLineEdit()
        self.qe_rate.setPlaceholderText("0.00")

        self.qe_total_pcs = QLineEdit()
        self.qe_total_pcs.setPlaceholderText("1")

        self.qe_amount = QLineEdit()
        self.qe_amount.setPlaceholderText("Amount (Auto)")
        self.qe_amount.setReadOnly(True)
        self.qe_amount.setStyleSheet("background-color: #E9ECEF; color: #495057; font-weight: bold;")

        self.btn_add = QPushButton("Add Item")

        quick_entry_layout.addLayout(create_qe_vbox("Item Name", self.qe_item_name))
        quick_entry_layout.addLayout(create_qe_vbox("Rate (₹)", self.qe_rate))
        quick_entry_layout.addLayout(create_qe_vbox("Total Pcs", self.qe_total_pcs))
        quick_entry_layout.addLayout(create_qe_vbox("Amount (₹)", self.qe_amount))

        # Add button with empty label above for alignment
        btn_vbox = QVBoxLayout()
        btn_vbox.setSpacing(4)
        btn_vbox.addWidget(QLabel(""))
        btn_vbox.addWidget(self.btn_add)
        quick_entry_layout.addLayout(btn_vbox)
        left_layout.addLayout(quick_entry_layout)

        # =========================================================
        # RIGHT SIDE PANEL
        # =========================================================
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.card_frame = QFrame()
        self.card_frame.setObjectName("cardFrame")
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(20)

        # Add Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.card_frame.setGraphicsEffect(shadow)

        # Grand Total (like live weight label)
        self.lbl_grand_total = QLabel("🛒 Grand Total\n₹ 0.00")
        self.lbl_grand_total.setObjectName("grandTotalLabel")
        self.lbl_grand_total.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.lbl_grand_total)

        # Panel Values
        self.lbl_total_items = self.create_panel_row(card_layout, "Total Items:", "0")
        self.lbl_total_pcs = self.create_panel_row(card_layout, "Total Pieces:", "0")
        self.lbl_current_amount = self.create_panel_row(card_layout, "Current Item Amount:", "₹ 0.00")

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet("background-color: #DEE2E6;")
        card_layout.addWidget(divider)

        # Discount Input
        discount_layout = QHBoxLayout()
        lbl_discount = QLabel("Discount (₹):")
        lbl_discount.setProperty("class", "panelLabel")
        self.inp_discount = QLineEdit()
        self.inp_discount.setAlignment(Qt.AlignRight)
        self.inp_discount.setText("0.00")
        discount_layout.addWidget(lbl_discount)
        discount_layout.addStretch()
        discount_layout.addWidget(self.inp_discount)
        card_layout.addLayout(discount_layout)

        # Divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setFrameShadow(QFrame.Sunken)
        divider2.setStyleSheet("background-color: #DEE2E6;")
        card_layout.addWidget(divider2)

        # Final Amount
        amount_layout = QVBoxLayout()
        lbl_amount_title = QLabel("Final Amount")
        lbl_amount_title.setProperty("class", "panelLabel")
        self.lbl_final_amount = QLabel("₹ 0.00")
        self.lbl_final_amount.setObjectName("amountLabel")
        self.lbl_final_amount.setAlignment(Qt.AlignRight)
        amount_layout.addWidget(lbl_amount_title)
        amount_layout.addWidget(self.lbl_final_amount)
        card_layout.addLayout(amount_layout)

        card_layout.addStretch()
        right_layout.addWidget(self.card_frame)

        # Add to main layout with stretch factors
        main_layout.addWidget(left_widget, stretch=7)
        main_layout.addWidget(right_widget, stretch=3)

    def create_panel_row(self, layout, title, default_val):
        row_layout = QHBoxLayout()
        lbl_title = QLabel(title)
        lbl_title.setProperty("class", "panelLabel")
        lbl_val = QLabel(default_val)
        lbl_val.setProperty("class", "panelValue")
        lbl_val.setAlignment(Qt.AlignRight)
        row_layout.addWidget(lbl_title)
        row_layout.addStretch()
        row_layout.addWidget(lbl_val)
        layout.addLayout(row_layout)
        return lbl_val

    def setup_connections(self):
        # Quick Entry live calculations
        self.qe_rate.textChanged.connect(self.calculate_current_amount)
        self.qe_total_pcs.textChanged.connect(self.calculate_current_amount)

        # Add / Delete buttons
        self.btn_add.clicked.connect(self.add_item_to_table)
        self.btn_remove.clicked.connect(self.remove_selected_item)
        self.btn_generate_pdf.clicked.connect(self.generate_pdf)

        # Discount recalculation
        self.inp_discount.textChanged.connect(self.calculate_totals)

    # ── Helpers ──

    def get_float(self, text, default=0.0):
        try:
            if not text.strip():
                return default
            return float(text)
        except ValueError:
            return default

    def calculate_current_amount(self):
        rate = self.get_float(self.qe_rate.text())
        pcs = self.get_float(self.qe_total_pcs.text(), 1.0)
        amount = rate * pcs
        self.qe_amount.setText(f"{amount:,.2f}")
        self.lbl_current_amount.setText(f"₹ {amount:,.2f}")

    def add_item_to_table(self):
        name = self.qe_item_name.text().strip() or "Item"
        rate = self.get_float(self.qe_rate.text())
        pcs = self.get_float(self.qe_total_pcs.text(), 1.0)
        amount = self.get_float(self.qe_amount.text().replace(",", ""))

        if rate <= 0:
            return

        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.table.setItem(row, 1, QTableWidgetItem(name))
        self.table.setItem(row, 2, QTableWidgetItem(f"{rate:,.2f}"))
        self.table.setItem(row, 3, QTableWidgetItem(f"{int(pcs)}"))
        self.table.setItem(row, 4, QTableWidgetItem(f"{amount:,.2f}"))

        # Clear quick entry
        self.qe_item_name.clear()
        self.qe_rate.clear()
        self.qe_total_pcs.clear()
        self.qe_amount.clear()

        self.calculate_totals()

    def remove_selected_item(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)
            # Re-number rows
            for r in range(self.table.rowCount()):
                self.table.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            self.calculate_totals()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete and self.table.hasFocus():
            self.remove_selected_item()
        super().keyPressEvent(event)

    def calculate_totals(self):
        total_amount = 0.0
        total_pcs = 0
        total_items = self.table.rowCount()

        for row in range(total_items):
            amt_item = self.table.item(row, 4)
            pcs_item = self.table.item(row, 3)
            if amt_item:
                total_amount += self.get_float(amt_item.text().replace(",", ""))
            if pcs_item:
                total_pcs += int(self.get_float(pcs_item.text()))

        discount = self.get_float(self.inp_discount.text())
        final_amount = total_amount - discount

        self.lbl_grand_total.setText(f"🛒 Grand Total\n₹ {total_amount:,.2f}")
        self.lbl_total_items.setText(str(total_items))
        self.lbl_total_pcs.setText(str(total_pcs))
        self.lbl_final_amount.setText(f"₹ {final_amount:,.2f}")

    # ── PDF Generation ──

    def generate_pdf(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "Please add items to the table before generating a bill.")
            return

        voucher = self.voucher_input.text().strip() or "N/A"
        date_str = self.date_input.date().toString("dd-MM-yyyy")
        party = self.party_input.text().strip() or "Walk-in Customer"
        grand_total = self.lbl_grand_total.text().split("\n")[-1].strip()
        discount = self.inp_discount.text().strip() or "0.00"
        final_amount = self.lbl_final_amount.text()

        default_name = f"ItemBill_{voucher}_{date_str}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Bill PDF", default_name, "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        try:
            self._build_pdf(file_path, voucher, date_str, party,
                            grand_total, discount, final_amount)
            QMessageBox.information(self, "Success", f"Bill saved successfully!\n{file_path}")
            os.startfile(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF.\n{str(e)}")

    def _build_pdf(self, file_path, voucher, date_str, party,
                   grand_total, discount, final_amount):
        doc = SimpleDocTemplate(
            file_path, pagesize=A4,
            topMargin=20*mm, bottomMargin=15*mm,
            leftMargin=15*mm, rightMargin=15*mm
        )
        elements = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'BillTitle', parent=styles['Title'],
            fontSize=22, leading=26, alignment=TA_CENTER,
            textColor=colors.HexColor('#212529'), spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'BillSubtitle', parent=styles['Normal'],
            fontSize=10, alignment=TA_CENTER,
            textColor=colors.HexColor('#6C757D'), spaceAfter=12
        )
        heading_style = ParagraphStyle(
            'SectionHead', parent=styles['Normal'],
            fontSize=12, leading=16, textColor=colors.HexColor('#495057'),
            spaceBefore=10, spaceAfter=6, fontName='Helvetica-Bold'
        )
        normal_style = ParagraphStyle(
            'BillNormal', parent=styles['Normal'],
            fontSize=10, leading=14, textColor=colors.HexColor('#343A40')
        )
        amount_style = ParagraphStyle(
            'AmountStyle', parent=styles['Normal'],
            fontSize=16, leading=20, alignment=TA_RIGHT,
            textColor=colors.HexColor('#2B8A3E'), fontName='Helvetica-Bold',
            spaceBefore=8
        )

        # ── Header ──
        elements.append(Paragraph("✦ ITEM BILL ✦", title_style))
        elements.append(Paragraph("Item-wise Billing Invoice", subtitle_style))
        elements.append(Spacer(1, 4*mm))

        # ── Bill Info ──
        info_data = [
            [Paragraph(f"<b>Voucher:</b> {voucher}", normal_style),
             Paragraph(f"<b>Date:</b> {date_str}", normal_style)],
            [Paragraph(f"<b>Party:</b> {party}", normal_style),
             Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%d-%m-%Y %I:%M %p')}", normal_style)],
        ]
        info_table = Table(info_data, colWidths=[doc.width/2]*2)
        info_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 6*mm))

        # ── Divider ──
        div_table = Table([[""]], colWidths=[doc.width])
        div_table.setStyle(TableStyle([
            ('LINEABOVE', (0,0), (-1,0), 1, colors.HexColor('#DEE2E6')),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(div_table)
        elements.append(Spacer(1, 4*mm))

        # ── Items Table ──
        elements.append(Paragraph("Item Details", heading_style))

        header_row = ["#", "Item Name", "Rate (₹)", "Total Pcs", "Amount (₹)"]
        table_data = [header_row]

        grand_total_val = 0.0
        total_pcs_val = 0

        for row in range(self.table.rowCount()):
            sr = self.table.item(row, 0).text() if self.table.item(row, 0) else str(row+1)
            name = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
            rate = self.table.item(row, 2).text() if self.table.item(row, 2) else "0"
            pcs = self.table.item(row, 3).text() if self.table.item(row, 3) else "0"
            amt = self.table.item(row, 4).text() if self.table.item(row, 4) else "0"

            grand_total_val += self.get_float(amt.replace(",", ""))
            total_pcs_val += int(self.get_float(pcs))

            table_data.append([sr, name, rate, pcs, amt])

        # Totals row
        table_data.append(["", "TOTAL", "", str(total_pcs_val), f"{grand_total_val:,.2f}"])

        col_widths = [35, 160, 80, 65, 90]
        items_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        items_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#343A40')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,0), (-1,0), 8),
            # Body
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('BOTTOMPADDING', (0,1), (-1,-1), 6),
            ('TOPPADDING', (0,1), (-1,-1), 6),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
            ('ALIGN', (2,0), (2,-1), 'RIGHT'),
            ('ALIGN', (3,0), (3,-1), 'CENTER'),
            ('ALIGN', (4,0), (4,-1), 'RIGHT'),
            # Alternating rows
            ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#F8F9FA')]),
            # Grid
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DEE2E6')),
            # Totals row
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#E9ECEF')),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('LINEABOVE', (0,-1), (-1,-1), 1.5, colors.HexColor('#343A40')),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 8*mm))

        # ── Summary ──
        elements.append(Paragraph("Bill Summary", heading_style))

        summary_data = [
            ["Grand Total", grand_total],
            ["Discount", f"₹ {discount}"],
        ]
        summary_table = Table(summary_data, colWidths=[doc.width*0.5, doc.width*0.5])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.HexColor('#E9ECEF')),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 4*mm))

        # ── Final Amount ──
        amount_div = Table([[""]], colWidths=[doc.width])
        amount_div.setStyle(TableStyle([
            ('LINEABOVE', (0,0), (-1,0), 2, colors.HexColor('#2B8A3E')),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(amount_div)
        elements.append(Paragraph(f"Final Amount: {final_amount}", amount_style))
        elements.append(Spacer(1, 12*mm))

        # ── Footer ──
        footer_style = ParagraphStyle(
            'Footer', parent=styles['Normal'],
            fontSize=8, alignment=TA_CENTER,
            textColor=colors.HexColor('#ADB5BD'), spaceBefore=15
        )
        elements.append(Paragraph("— Thank you for your business —", footer_style))
        elements.append(Paragraph("This is a computer-generated bill.", footer_style))

        doc.build(elements)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ItemBillingPage()
    window.resize(1100, 700)
    window.show()
    sys.exit(app.exec_())
