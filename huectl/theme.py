"""Application dark theme."""

ACCENT = "#f0b429"


def theme():
    return f"""
QWidget {{ background: #16181d; color: #e6e6e6; font-size: 13px; }}
QScrollArea {{ background: transparent; border: 0; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QGroupBox {{
    border: 1px solid #262a31; border-radius: 12px;
    margin-top: 16px; padding: 12px; background: #1c1f26;
}}
QGroupBox::title {{
    subcontrol-origin: margin; left: 14px; padding: 0 5px;
    color: {ACCENT}; font-weight: 700;
}}
QPushButton {{
    background: #262a31; border: 1px solid #313742; border-radius: 8px;
    padding: 6px 12px;
}}
QPushButton:hover {{ background: #2f343d; border-color: #444b57; }}
QPushButton:pressed {{ background: #21252b; }}
QLineEdit, QComboBox {{
    background: #12141a; border: 1px solid #2a2f38; border-radius: 8px; padding: 6px;
}}
QComboBox::drop-down {{ border: 0; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
    width: 20px; height: 20px; border-radius: 5px;
    border: 1px solid #3a4049; background: #12141a;
}}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QSlider::groove:horizontal {{ height: 6px; background: #2a2f38; border-radius: 3px; }}
QSlider::handle:horizontal {{
    width: 16px; margin: -6px 0; border-radius: 8px; background: {ACCENT};
}}
QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 3px; }}
QMenu {{ background: #1c1f26; border: 1px solid #2a2f38; padding: 4px; }}
QMenu::item {{ padding: 5px 22px; border-radius: 6px; }}
QMenu::item:selected {{ background: #2f343d; }}
QLabel {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #313742; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QToolTip {{ background: #1c1f26; color: #e6e6e6; border: 1px solid #2a2f38; }}
"""
