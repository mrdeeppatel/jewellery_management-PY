import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QDateEdit,
    QApplication, QGraphicsDropShadowEffect, QSizePolicy, QAbstractItemView,
    QFileDialog, QMessageBox, QScrollArea, QComboBox
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont, QColor
from models.database import get_db, Item
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


class LiveBillingPage(QWidget):
    def __init__(self):
        super().__init__()
        self._prev_code_len = 0   # track field length to detect erase
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        self.setWindowTitle("Live Billing Panel")
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
            #liveWeightLabel {
                font-size: 24px;
                font-weight: bold;
                color: #E03131;
                padding: 15px;
                background-color: #FFF5F5;
                border-radius: 8px;
                border: 2px dashed #FFA8A8;
            }
            .panelLabel {
                font-size: 14px;
                color: #495057;
            }
            .panelValue {
                font-size: 16px;
                font-weight: bold;
                color: #212529;
            }
            .headerLabel {
                font-size: 20px;
                font-weight: bold;
                color: #212529;
                margin-bottom: 10px;
            }
            #entryCard {
                background-color: #F8F9FA;
                border: 1px solid #E9ECEF;
                border-radius: 8px;
                padding: 8px;
                margin-bottom: 4px;
            }
            #remainingLabel {
                font-size: 15px;
                font-weight: bold;
                color: #E03131;
                padding: 6px 10px;
                background-color: #FFF5F5;
                border-radius: 6px;
                border: 1px solid #FFD8D8;
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

        # 2. Input Fields
        input_fields_layout = QHBoxLayout()
        input_fields_layout.setSpacing(15)
        
        self.global_touch_input = QLineEdit()
        self.global_touch_input.setPlaceholderText("100.00")
        self.global_touch_input.setText("100.00")
        
        self.global_wastage_input = QLineEdit()
        self.global_wastage_input.setPlaceholderText("0.00")
        self.global_wastage_input.setText("0.00")
        
        self.global_tag_input = QLineEdit()
        self.global_tag_input.setPlaceholderText("Tag Number")
        
        input_fields_layout.addWidget(QLabel("Global Touch (%):"))
        input_fields_layout.addWidget(self.global_touch_input)
        input_fields_layout.addWidget(QLabel("Global Wastage (%):"))
        input_fields_layout.addWidget(self.global_wastage_input)
        input_fields_layout.addWidget(QLabel("Global Tag:"))
        input_fields_layout.addWidget(self.global_tag_input)
        left_layout.addLayout(input_fields_layout)

        # 3. Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["TagNo / Design", "Item Name", "Net Weight", "Touch", "Wastage", "Fine", "D"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        left_layout.addWidget(self.table)
        
        # Table Controls
        table_controls_layout = QHBoxLayout()
        self.btn_remove = QPushButton("🗑 Delete Selected")
        self.btn_remove.setStyleSheet("background-color: #FA5252; color: white; padding: 6px 12px; font-size: 13px; font-weight: bold; border-radius: 4px;")
        self.btn_generate_pdf = QPushButton("📄 Generate PDF Bill")
        self.btn_generate_pdf.setStyleSheet("background-color: #2B8A3E; color: white; padding: 6px 14px; font-size: 13px; font-weight: bold; border-radius: 4px;")
        table_controls_layout.addWidget(self.btn_generate_pdf)
        table_controls_layout.addStretch()
        table_controls_layout.addWidget(self.btn_remove)
        left_layout.addLayout(table_controls_layout)

        # 4. Quick Entry Row
        qe_header_layout = QHBoxLayout()
        qe_title = QLabel("Quick Entry:")
        qe_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #495057;")
        qe_header_layout.addWidget(qe_title)
        
        self.lbl_qe_selected_item = QLabel("")
        self.lbl_qe_selected_item.setStyleSheet("font-weight: bold; font-size: 14px; color: #2B8A3E;")
        qe_header_layout.addWidget(self.lbl_qe_selected_item)
        qe_header_layout.addStretch()
        
        left_layout.addLayout(qe_header_layout)
        
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
        
        self.qe_item_code = QLineEdit()
        self.qe_item_code.setPlaceholderText("🔍  Item Code / Name")

        self.qe_net_weight = QLineEdit()
        self.qe_net_weight.setPlaceholderText("Net Wt")
        
        self.qe_touch = QLineEdit()
        self.qe_touch.setPlaceholderText("Touch %")
        
        self.qe_wastage = QLineEdit()
        self.qe_wastage.setPlaceholderText("Wastage %")
        
        self.qe_fine = QLineEdit()
        self.qe_fine.setPlaceholderText("Fine (Auto)")
        self.qe_fine.setReadOnly(True)
        self.qe_fine.setStyleSheet("background-color: #E9ECEF; color: #495057; font-weight: bold;")
        
        self.btn_add = QPushButton("Add Item")

        quick_entry_layout.addLayout(create_qe_vbox("Item Code", self.qe_item_code))
        quick_entry_layout.addLayout(create_qe_vbox("Net Wt", self.qe_net_weight))
        quick_entry_layout.addLayout(create_qe_vbox("Touch %", self.qe_touch))
        quick_entry_layout.addLayout(create_qe_vbox("Wastage %", self.qe_wastage))
        quick_entry_layout.addLayout(create_qe_vbox("Fine", self.qe_fine))
        
        # Add button with empty label above it to align correctly
        btn_vbox = QVBoxLayout()
        btn_vbox.setSpacing(4)
        btn_vbox.addWidget(QLabel(""))
        btn_vbox.addWidget(self.btn_add)
        quick_entry_layout.addLayout(btn_vbox)
        left_layout.addLayout(quick_entry_layout)

        # ── Live Autocomplete Dropdown (floats above the input) ──────────────
        # Parent is self (the top-level widget) so it can overlap everything.
        self.suggestion_frame = QFrame(self)
        self.suggestion_frame.setObjectName("suggestionFrame")
        self.suggestion_frame.setStyleSheet("""
            QFrame#suggestionFrame {
                background-color: #ffffff;
                border: 1.5px solid #4DABF7;
                border-radius: 8px;
            }
        """)
        sug_layout = QVBoxLayout(self.suggestion_frame)
        sug_layout.setContentsMargins(0, 0, 0, 0)
        sug_layout.setSpacing(0)

        # Header row: title + close button
        sug_header = QWidget()
        sug_header.setStyleSheet("background-color: #E7F5FF; border-radius: 8px;")
        sug_header_layout = QHBoxLayout(sug_header)
        sug_header_layout.setContentsMargins(10, 4, 6, 4)
        sug_lbl = QLabel("Matching Items")
        sug_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #1971C2;")
        self.btn_close_sug = QPushButton("✕")
        self.btn_close_sug.setFixedSize(22, 22)
        self.btn_close_sug.setStyleSheet(
            "QPushButton { background-color: transparent; color: #868E96; font-size: 13px; font-weight: bold; border: none; border-radius: 4px; }"
            "QPushButton:hover { background-color: #FA5252; color: white; }"
        )
        self.btn_close_sug.setCursor(Qt.PointingHandCursor)
        sug_header_layout.addWidget(sug_lbl)
        sug_header_layout.addStretch()
        sug_header_layout.addWidget(self.btn_close_sug)
        sug_layout.addWidget(sug_header)

        # Scrollable list of suggestion rows
        self.sug_scroll = QScrollArea()
        self.sug_scroll.setWidgetResizable(True)
        self.sug_scroll.setFrameShape(QFrame.NoFrame)
        self.sug_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sug_inner = QWidget()
        self.sug_inner_layout = QVBoxLayout(self.sug_inner)
        self.sug_inner_layout.setContentsMargins(0, 0, 0, 0)
        self.sug_inner_layout.setSpacing(0)
        self.sug_scroll.setWidget(self.sug_inner)
        sug_layout.addWidget(self.sug_scroll)

        self.suggestion_frame.hide()

        # Debounce timer
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)

        # =========================================================
        # RIGHT SIDE PANEL — Gold Calculation System
        # =========================================================
        self.calc_entries = []  # list of entry widget dicts

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Scrollable card so it works on smaller screens
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.NoFrame)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        right_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.card_frame = QFrame()
        self.card_frame.setObjectName("cardFrame")
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)

        # Add Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.card_frame.setGraphicsEffect(shadow)

        # ── Section: Initial Total Fine (auto from table) ──
        header_lbl = QLabel("⚖️ Gold Calculation")
        header_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529;")
        card_layout.addWidget(header_lbl)

        self.lbl_total_fine = self.create_panel_row(card_layout, "Total Fine (from items):", "0.000 g")
        self.lbl_current_fine = self.create_panel_row(card_layout, "Fine (current item):", "0.000 g")

        # Thin divider
        card_layout.addWidget(self._make_divider())

        # ── Section: Dynamic Entries ──
        entry_header_layout = QHBoxLayout()
        entry_title = QLabel("📝 Settlement Entries")
        entry_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #495057;")
        self.btn_add_entry = QPushButton("+ Add Entry")
        self.btn_add_entry.setFixedHeight(30)
        self.btn_add_entry.setStyleSheet(
            "QPushButton { background-color: #339AF0; color: white; padding: 4px 14px; font-size: 13px; "
            "font-weight: bold; border-radius: 5px; border: none; }"
            "QPushButton:hover { background-color: #228BE6; }"
        )
        entry_header_layout.addWidget(entry_title)
        entry_header_layout.addStretch()
        entry_header_layout.addWidget(self.btn_add_entry)
        card_layout.addLayout(entry_header_layout)

        # Container for dynamic entry cards
        self.entries_container = QVBoxLayout()
        self.entries_container.setSpacing(6)
        card_layout.addLayout(self.entries_container)

        # Remaining balance label
        self.lbl_remaining = QLabel("Remaining: 0.000 g")
        self.lbl_remaining.setObjectName("remainingLabel")
        self.lbl_remaining.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.lbl_remaining)

        # Thin divider
        card_layout.addWidget(self._make_divider())

        # ── Section: Summary ──
        summary_lbl = QLabel("📊 Summary")
        summary_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #495057;")
        card_layout.addWidget(summary_lbl)

        self.lbl_total_entry_fine = self.create_panel_row(card_layout, "Total Entry Fine:", "0.000 g")
        self.lbl_9950_fine = self.create_panel_row(card_layout, "99.50 Fine:", "0.000 g")

        # Rate Cut Input
        rate_layout = QHBoxLayout()
        lbl_rate = QLabel("Rate Cut (per 10 gm):")
        lbl_rate.setProperty("class", "panelLabel")
        self.inp_rate_cut = QLineEdit()
        self.inp_rate_cut.setAlignment(Qt.AlignRight)
        self.inp_rate_cut.setText("0.00")
        self.inp_rate_cut.setFixedWidth(120)
        rate_layout.addWidget(lbl_rate)
        rate_layout.addStretch()
        rate_layout.addWidget(self.inp_rate_cut)
        card_layout.addLayout(rate_layout)

        # Divider before amount
        card_layout.addWidget(self._make_divider())

        # Amount
        amount_layout = QVBoxLayout()
        lbl_amount_title = QLabel("Final Price")
        lbl_amount_title.setProperty("class", "panelLabel")
        self.lbl_amount = QLabel("₹ 0.00")
        self.lbl_amount.setObjectName("amountLabel")
        self.lbl_amount.setAlignment(Qt.AlignRight)
        amount_layout.addWidget(lbl_amount_title)
        amount_layout.addWidget(self.lbl_amount)
        card_layout.addLayout(amount_layout)

        card_layout.addStretch()

        right_scroll.setWidget(self.card_frame)
        right_layout.addWidget(right_scroll)

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

    def _make_divider(self):
        """Create a thin horizontal divider line."""
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet("background-color: #DEE2E6; max-height: 1px;")
        return divider

    # ── Dynamic entry management ──────────────────────────────────────────
    def _add_calc_entry(self):
        """Add a new settlement entry card to the right panel."""
        entry_idx = len(self.calc_entries)

        frame = QFrame()
        frame.setObjectName("entryCard")
        frame.setStyleSheet("""
            QFrame#entryCard {
                background-color: #F8F9FA;
                border: 1px solid #E9ECEF;
                border-radius: 8px;
                padding: 6px;
            }
        """)
        v_layout = QVBoxLayout(frame)
        v_layout.setContentsMargins(10, 8, 10, 8)
        v_layout.setSpacing(6)

        # Row 1: Entry header + type selector + remove btn
        row1 = QHBoxLayout()
        lbl_num = QLabel(f"Entry #{entry_idx + 1}")
        lbl_num.setStyleSheet("font-weight: bold; font-size: 13px; color: #495057;")

        combo_type = QComboBox()
        combo_type.addItems(["Gold + Purity", "Direct Fine"])
        combo_type.setFixedWidth(130)
        combo_type.setStyleSheet("padding: 4px 8px; font-size: 13px; border-radius: 4px;")

        btn_remove = QPushButton("✕")
        btn_remove.setFixedSize(24, 24)
        btn_remove.setStyleSheet(
            "QPushButton { background-color: transparent; color: #868E96; font-size: 14px; "
            "font-weight: bold; border: none; border-radius: 4px; padding: 0px; }"
            "QPushButton:hover { background-color: #FA5252; color: white; }"
        )
        btn_remove.setCursor(Qt.PointingHandCursor)

        row1.addWidget(lbl_num)
        row1.addStretch()
        row1.addWidget(combo_type)
        row1.addWidget(btn_remove)
        v_layout.addLayout(row1)

        # Row 2: Weight / Fine input + Purity input
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        inp_weight = QLineEdit()
        inp_weight.setPlaceholderText("Weight (g)")
        inp_weight.setStyleSheet("padding: 6px 8px; font-size: 13px;")

        inp_purity = QLineEdit()
        inp_purity.setPlaceholderText("Purity %")
        inp_purity.setText("99.50")
        inp_purity.setStyleSheet("padding: 6px 8px; font-size: 13px;")

        row2.addWidget(inp_weight, stretch=1)
        row2.addWidget(inp_purity, stretch=1)
        v_layout.addLayout(row2)

        # Row 3: Computed fine display
        lbl_fine = QLabel("Fine: 0.000 g")
        lbl_fine.setStyleSheet("font-size: 13px; font-weight: bold; color: #2B8A3E;")
        lbl_fine.setAlignment(Qt.AlignRight)
        v_layout.addWidget(lbl_fine)

        # Store entry dict
        entry = {
            "frame": frame,
            "combo_type": combo_type,
            "inp_weight": inp_weight,
            "inp_purity": inp_purity,
            "lbl_fine": lbl_fine,
            "lbl_num": lbl_num,
        }
        self.calc_entries.append(entry)
        self.entries_container.addWidget(frame)

        # Connect signals for real-time updates
        inp_weight.textChanged.connect(self._recalc_entries)
        inp_purity.textChanged.connect(self._recalc_entries)
        combo_type.currentIndexChanged.connect(lambda: self._on_entry_type_changed(entry))

        # Remove button
        def remove_this():
            self.calc_entries.remove(entry)
            frame.setParent(None)
            frame.deleteLater()
            self._renumber_entries()
            self._recalc_entries()

        btn_remove.clicked.connect(remove_this)

        # Trigger type change to set initial state
        self._on_entry_type_changed(entry)
        self._recalc_entries()

    def _on_entry_type_changed(self, entry):
        """Toggle between Gold+Purity and Direct Fine modes."""
        is_direct = entry["combo_type"].currentText() == "Direct Fine"
        if is_direct:
            entry["inp_weight"].setPlaceholderText("Fine (g)")
            entry["inp_purity"].setText("100.00")
            entry["inp_purity"].setEnabled(False)
            entry["inp_purity"].setStyleSheet("padding: 6px 8px; font-size: 13px; background-color: #E9ECEF; color: #868E96;")
        else:
            entry["inp_weight"].setPlaceholderText("Weight (g)")
            entry["inp_purity"].setEnabled(True)
            entry["inp_purity"].setStyleSheet("padding: 6px 8px; font-size: 13px;")
            if entry["inp_purity"].text() == "100.00":
                entry["inp_purity"].setText("99.50")
        self._recalc_entries()

    def _renumber_entries(self):
        """Re-number entry labels after removal."""
        for i, entry in enumerate(self.calc_entries):
            entry["lbl_num"].setText(f"Entry #{i + 1}")

    def _recalc_entries(self):
        """Recalculate fine for each entry and update remaining / totals."""
        # Get total fine from the items table
        table_total_fine = 0.0
        for row in range(self.table.rowCount()):
            fine_item = self.table.item(row, 5)
            if fine_item:
                table_total_fine += self.get_float(fine_item.text())
        self.lbl_total_fine.setText(f"{table_total_fine:.3f} g")

        total_entry_fine = 0.0
        remaining = table_total_fine

        for entry in self.calc_entries:
            weight = self.get_float(entry["inp_weight"].text())
            purity = self.get_float(entry["inp_purity"].text())
            is_direct = entry["combo_type"].currentText() == "Direct Fine"

            if is_direct:
                fine_val = weight  # direct fine
            else:
                fine_val = (weight * purity) / 100.0

            entry["lbl_fine"].setText(f"Fine: {fine_val:.3f} g")
            total_entry_fine += fine_val
            remaining -= fine_val

        self.lbl_total_entry_fine.setText(f"{total_entry_fine:.3f} g")

        # Remaining
        if remaining < 0:
            self.lbl_remaining.setText(f"Remaining: {remaining:.3f} g  (OVER)")
            self.lbl_remaining.setStyleSheet(
                "font-size: 15px; font-weight: bold; color: #E03131; padding: 6px 10px; "
                "background-color: #FFF5F5; border-radius: 6px; border: 1px solid #FFD8D8;"
            )
        else:
            self.lbl_remaining.setText(f"Remaining: {remaining:.3f} g")
            self.lbl_remaining.setStyleSheet(
                "font-size: 15px; font-weight: bold; color: #1971C2; padding: 6px 10px; "
                "background-color: #E7F5FF; border-radius: 6px; border: 1px solid #A5D8FF;"
            )

        # 99.50 Fine calculation
        global_touch = self.get_float(self.global_touch_input.text(), 100.0)
        if global_touch > 0:
            pure_fine = (table_total_fine * 99.5) / global_touch
        else:
            pure_fine = 0.0
        self.lbl_9950_fine.setText(f"{pure_fine:.3f} g")

        # Final Price based on Remaining balance
        rate_10g = self.get_float(self.inp_rate_cut.text())
        rate_per_gram = rate_10g / 10.0
        final_price = remaining * rate_per_gram
        if final_price < 0:
            self.lbl_amount.setText(f"- ₹ {abs(final_price):,.2f}")
            self.lbl_amount.setStyleSheet("font-size: 32px; font-weight: bold; color: #E03131;")
        else:
            self.lbl_amount.setText(f"₹ {final_price:,.2f}")
            self.lbl_amount.setStyleSheet("font-size: 32px; font-weight: bold; color: #2B8A3E;")

    def setup_connections(self):
        # When global touch/wastage change, pre-fill quick entry if empty
        self.global_touch_input.textChanged.connect(self.populate_quick_entry_defaults)
        self.global_wastage_input.textChanged.connect(self.populate_quick_entry_defaults)
        
        # Quick Entry calculations
        self.qe_net_weight.textChanged.connect(self.calculate_current_fine)
        self.qe_touch.textChanged.connect(self.calculate_current_fine)
        self.qe_wastage.textChanged.connect(self.calculate_current_fine)
        
        # Add button
        self.btn_add.clicked.connect(self.add_item_to_table)
        self.btn_remove.clicked.connect(self.remove_selected_item)
        self.btn_generate_pdf.clicked.connect(self.generate_pdf)
        
        # Live autocomplete
        self.qe_item_code.textChanged.connect(self._on_code_changed)
        self.btn_close_sug.clicked.connect(self.hide_suggestions)

        # Rate calculation
        self.inp_rate_cut.textChanged.connect(self._recalc_entries)

        # Add entry button
        self.btn_add_entry.clicked.connect(self._add_calc_entry)

    def populate_quick_entry_defaults(self):
        if not self.qe_touch.text():
            self.qe_touch.setText(self.global_touch_input.text())
        if not self.qe_wastage.text():
            self.qe_wastage.setText(self.global_wastage_input.text())

    def get_float(self, text, default=0.0):
        try:
            if not text.strip():
                return default
            return float(text)
        except ValueError:
            return default

    def calculate_current_fine(self):
        net_wt = self.get_float(self.qe_net_weight.text())
        touch = self.get_float(self.qe_touch.text())
        wastage = self.get_float(self.qe_wastage.text())
        
        # Combine Touch and Wastage
        effective_percent = touch + wastage
        
        # Fine = Net Weight * (Effective % / 100)
        fine = net_wt * (effective_percent / 100.0)
        
        self.qe_fine.setText(f"{fine:.3f}")
        self.lbl_current_fine.setText(f"{fine:.3f} g")

    def add_item_to_table(self):
        code = self.qe_item_code.text().strip() or "Item"
        net_wt = self.get_float(self.qe_net_weight.text())
        touch = self.get_float(self.qe_touch.text())
        wastage = self.get_float(self.qe_wastage.text())
        fine = self.get_float(self.qe_fine.text())
        
        if net_wt <= 0:
            return
            
        tag = getattr(self, '_current_selected_tag', None) or self.global_tag_input.text() or "T-001"
        name = getattr(self, '_current_selected_name', None) or code
            
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(tag))
        self.table.setItem(row, 1, QTableWidgetItem(name))
        self.table.setItem(row, 2, QTableWidgetItem(f"{net_wt:.3f}"))
        self.table.setItem(row, 3, QTableWidgetItem(f"{touch:.2f}"))
        self.table.setItem(row, 4, QTableWidgetItem(f"{wastage:.2f}"))
        self.table.setItem(row, 5, QTableWidgetItem(f"{fine:.3f}"))
        self.table.setItem(row, 6, QTableWidgetItem("N")) # Optional flag
        
        # Clear quick entry
        self.qe_item_code.clear()
        self.qe_net_weight.clear()
        self.qe_fine.clear()
        self.qe_touch.setText(self.global_touch_input.text())
        self.qe_wastage.setText(self.global_wastage_input.text())
        if hasattr(self, 'lbl_qe_selected_item'):
            self.lbl_qe_selected_item.clear()
        self._current_selected_tag = None
        self._current_selected_name = None
        
        self.calculate_totals()

    def remove_selected_item(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)
            self.calculate_totals()

    # ── Live autocomplete helpers ─────────────────────────────────────────
    def _on_code_changed(self, text):
        new_len = len(text)
        erasing = new_len < self._prev_code_len   # user deleted characters
        self._prev_code_len = new_len

        # Clear selected item info if user manually edits
        if hasattr(self, 'lbl_qe_selected_item'):
            self.lbl_qe_selected_item.clear()
        self._current_selected_tag = None
        self._current_selected_name = None

        # Always hide & stop when field is empty or user is erasing
        if not text.strip() or erasing:
            self._search_timer.stop()
            self.hide_suggestions()
            return

        self._search_timer.stop()
        self._search_timer.timeout.disconnect() if self._search_timer.receivers(self._search_timer.timeout) else None
        self._search_timer.timeout.connect(lambda: self._do_live_search(text.strip()))
        self._search_timer.start()

    def _do_live_search(self, query):
        try:
            db = next(get_db())
            results = db.query(Item).filter(
                (Item.item_code.ilike(f"%{query}%")) |
                (Item.item_name.ilike(f"%{query}%")) |
                (Item.tag_no.ilike(f"%{query}%")) |
                (Item.design.ilike(f"%{query}%"))
            ).limit(10).all()
            db.close()
        except Exception:
            self.hide_suggestions()
            return

        if not results:
            self.hide_suggestions()
            return

        if len(results) == 1:
            # Single match — auto-fill (only reached when typing forward)
            self.hide_suggestions()
            self._apply_item(results[0])
            return

        self._populate_suggestions(results)

    def _populate_suggestions(self, items):
        # Clear old rows
        while self.sug_inner_layout.count():
            child = self.sug_inner_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for item in items:
            code = item.item_code or "-"
            tag = item.tag_no or "N/A"
            net = f"{item.net_wt} g" if item.net_wt else "-"
            touch = f"{item.touch}%" if item.touch else "-"
            design = f" | {item.design}" if item.design else ""
            label_text = f"<b>{code}</b>  {item.item_name}{design}   <span style='color:#868E96'>Tag: <b style='color:#495057'>{tag}</b> | Net: {net} | Touch: {touch}</span>"

            row_btn = QPushButton()
            row_btn.setText("")
            row_btn.setFlat(True)
            row_btn.setCursor(Qt.PointingHandCursor)
            row_btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px 12px;
                    border: none;
                    border-bottom: 1px solid #F1F3F5;
                    background-color: white;
                    font-size: 13px;
                }
                QPushButton:hover { background-color: #E7F5FF; }
            """)

            # Use a label inside the button for rich text
            btn_layout = QHBoxLayout(row_btn)
            btn_layout.setContentsMargins(8, 4, 8, 4)
            lbl = QLabel(label_text)
            lbl.setTextFormat(Qt.RichText)
            lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            btn_layout.addWidget(lbl)

            # Capture item in closure
            def make_slot(it):
                return lambda: self._select_suggestion(it)

            row_btn.clicked.connect(make_slot(item))
            self.sug_inner_layout.addWidget(row_btn)

        self.sug_inner_layout.addStretch()
        self._position_suggestion_frame()
        self.suggestion_frame.show()
        self.suggestion_frame.raise_()

    def _select_suggestion(self, item):
        self.hide_suggestions()
        self._apply_item(item)

    def _apply_item(self, item):
        # Block textChanged so we don't re-trigger search
        self.qe_item_code.blockSignals(True)
        self.qe_item_code.setText(item.item_code or item.item_name)
        self.qe_item_code.blockSignals(False)

        tag = item.tag_no or "N/A"
        name = item.item_name or "Unknown"
        if hasattr(self, 'lbl_qe_selected_item'):
            self.lbl_qe_selected_item.setText(f"✓ Selected: {name} | Tag: {tag}")
        self._current_selected_tag = item.tag_no
        self._current_selected_name = item.item_name

        if item.net_wt:
            self.qe_net_weight.setText(str(item.net_wt))
        if item.touch:
            self.qe_touch.setText(str(item.touch))
        self.calculate_current_fine()

    def hide_suggestions(self):
        self.suggestion_frame.hide()

    def _position_suggestion_frame(self):
        """Position the dropdown frame above the qe_item_code input."""
        input_global = self.qe_item_code.mapTo(self, self.qe_item_code.rect().topLeft())
        frame_h = min(220, 40 + self.sug_inner_layout.count() * 42)
        frame_w = max(self.qe_item_code.width() * 3, 480)
        x = input_global.x()
        y = input_global.y() - frame_h - 4
        # Keep inside widget
        if y < 0:
            y = input_global.y() + self.qe_item_code.height() + 4
        if x + frame_w > self.width():
            x = self.width() - frame_w - 4
        self.suggestion_frame.setGeometry(x, y, frame_w, frame_h)

    def resizeEvent(self, event):
        if not self.suggestion_frame.isHidden():
            self._position_suggestion_frame()
        super().resizeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete and self.table.hasFocus():
            self.remove_selected_item()
        super().keyPressEvent(event)

    def calculate_totals(self):
        """Recalculate all totals — delegates to _recalc_entries."""
        self._recalc_entries()

    def generate_pdf(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "Please add items to the table before generating a bill.")
            return

        # Gather bill info
        voucher = self.voucher_input.text().strip() or "N/A"
        date_str = self.date_input.date().toString("dd-MM-yyyy")
        party = self.party_input.text().strip() or "Walk-in Customer"
        total_fine = self.lbl_total_fine.text()
        fine_9950 = self.lbl_9950_fine.text()
        rate_cut = self.inp_rate_cut.text().strip() or "0.00"
        amount = self.lbl_amount.text()

        # Ask user where to save
        default_name = f"Bill_{voucher}_{date_str}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Bill PDF", default_name, "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        try:
            self._save_bill_to_db(voucher, party, total_fine, fine_9950, rate_cut, amount)
            self._build_pdf(file_path, voucher, date_str, party,
                            total_fine, fine_9950, rate_cut, amount)
            QMessageBox.information(self, "Success", f"Bill saved to DB and PDF generated successfully!\n{file_path}")
            os.startfile(file_path)  # Open the PDF on Windows
            
            # Optionally reset UI after bill is completed
            self.table.setRowCount(0)
            self.calculate_totals()
            self.voucher_input.clear()
            self.party_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save/generate bill.\n{str(e)}")

    def _save_bill_to_db(self, voucher, party, total_fine_str, fine_9950_str, rate_cut_str, amount_str):
        from models.database import Bill, BillItem
        db = next(get_db())
        try:
            total_fine = self.get_float(total_fine_str.replace(" g", ""))
            fine_9950 = self.get_float(fine_9950_str.replace(" g", ""))
            rate_cut = self.get_float(rate_cut_str)
            amount = self.get_float(amount_str.replace("₹", "").replace(",", "").strip())

            new_bill = Bill(
                voucher=voucher if voucher != "N/A" else None,
                customer_name=party,
                total_amount=amount,
                total_fine=total_fine,
                fine_9950=fine_9950,
                rate_cut=rate_cut,
                is_estimate=False
            )
            db.add(new_bill)
            db.commit()

            for row in range(self.table.rowCount()):
                tag = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
                name = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
                net_wt = self.get_float(self.table.item(row, 2).text() if self.table.item(row, 2) else "0")
                touch = self.get_float(self.table.item(row, 3).text() if self.table.item(row, 3) else "0")
                wastage = self.get_float(self.table.item(row, 4).text() if self.table.item(row, 4) else "0")
                fine = self.get_float(self.table.item(row, 5).text() if self.table.item(row, 5) else "0")

                b_item = BillItem(
                    bill_id=new_bill.id,
                    price=0.0,
                    tag=tag,
                    name=name,
                    net_wt=net_wt,
                    touch=touch,
                    wastage=wastage,
                    fine=fine
                )
                db.add(b_item)
            
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

    def _build_pdf(self, file_path, voucher, date_str, party,
                   total_fine, fine_9950, rate_cut, amount):
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os

        # ── Register Gujarati-capable font ──
        font_path = r'C:\Windows\Fonts\shruti.ttf'
        font_bold_path = r'C:\Windows\Fonts\shrutib.ttf'
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Shruti', font_path))
        if os.path.exists(font_bold_path):
            pdfmetrics.registerFont(TTFont('ShrutiBold', font_bold_path))

        guj_font = 'Shruti' if os.path.exists(font_path) else 'Helvetica'
        guj_bold = 'ShrutiBold' if os.path.exists(font_bold_path) else 'Helvetica-Bold'

        # A5 landscape-ish receipt (A5 portrait)
        from reportlab.lib.pagesizes import A5
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
        time_str = now.strftime('%I:%M:%S %p')
        header_data = [[
            f"Time: {time_str}",
            f"Date: {date_str}",
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

        # Collect data from table
        rate_val = self.get_float(rate_cut)
        rate_per_gram = rate_val / 10.0

        table_data = [headers]
        total_gross = 0.0
        total_less = 0.0
        total_net = 0.0
        total_fine_val = 0.0
        total_amount = 0.0

        for row in range(self.table.rowCount()):
            tag = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
            name = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
            net_wt = self.get_float(self.table.item(row, 2).text() if self.table.item(row, 2) else "0")
            touch = self.get_float(self.table.item(row, 3).text() if self.table.item(row, 3) else "0")
            wastage = self.get_float(self.table.item(row, 4).text() if self.table.item(row, 4) else "0")
            fine = self.get_float(self.table.item(row, 5).text() if self.table.item(row, 5) else "0")

            detail = f"{tag}" if tag else name
            gross = net_wt
            less = 0.0
            net = gross - less
            row_amount = fine * rate_per_gram

            total_gross += gross
            total_less += less
            total_net += net
            total_fine_val += fine
            total_amount += row_amount

            table_data.append([
                detail,
                f"{gross:.3f}",
                f"{less:.3f}",
                f"{net:.3f}",
                f"{touch:.2f}",
                f"{fine:.3f}",
                f"{rate_val:.0f}" if rate_val > 0 else "",
                f"{row_amount:.2f}" if rate_val > 0 else ""
            ])

        # Total row
        table_data.append([
            "Total",
            f"{total_gross:.3f}",
            f"{total_less:.3f}",
            f"{total_net:.3f}",
            "",
            f"{total_fine_val:.3f}",
            "",
            f"{total_amount:.2f}" if rate_val > 0 else ""
        ])

        cw = [usable_w*0.14, usable_w*0.12, usable_w*0.10, usable_w*0.12,
              usable_w*0.09, usable_w*0.13, usable_w*0.12, usable_w*0.18]
        items_table = Table(table_data, colWidths=cw, repeatRows=1)

        num_rows = len(table_data)
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
            # Bold total row
            ('FONTNAME', (0, num_rows-1), (-1, num_rows-1), guj_bold),
            ('LINEABOVE', (0, num_rows-1), (-1, num_rows-1), 1.2, black),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 4*mm))

        # ── Bottom Summary Section ──
        remaining_text = self.lbl_remaining.text().replace("Remaining: ", "").strip()
        qty = self.table.rowCount()

        bottom_data = [
            [f"P. Wt: {total_gross:.3f} g", f"Qty: {qty}",
             "\u0aac\u0abe\u0a95\u0ac0: " + remaining_text]  # બાકી
        ]
        bt = Table(bottom_data, colWidths=[usable_w*0.35, usable_w*0.25, usable_w*0.40])
        bt.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), guj_bold),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('TEXTCOLOR', (0,0), (-1,-1), black),
            ('BOX', (0,0), (-1,-1), 0.6, black),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ]))
        elements.append(bt)

        # Final Price row
        final_price_text = self.lbl_amount.text()
        fp_data = [[f"Final Price: {final_price_text}"]]
        fp = Table(fp_data, colWidths=[usable_w])
        fp.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), guj_bold),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('TEXTCOLOR', (0,0), (-1,-1), black),
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ('BOX', (0,0), (-1,-1), 0.6, black),
        ]))
        elements.append(fp)

        elements.append(Spacer(1, 3*mm))

        # Timestamp
        styles = getSampleStyleSheet()
        ts_style = ParagraphStyle(
            'Timestamp', parent=styles['Normal'],
            fontSize=6, alignment=TA_CENTER,
            textColor=black
        )
        elements.append(Paragraph(
            f"Generated: {now.strftime('%d-%m-%Y %I:%M:%S %p')}",
            ts_style
        ))

        doc.build(elements)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LiveBillingPage()
    window.resize(1100, 700)
    window.show()
    sys.exit(app.exec_())
