"""
SharpPic-AI — Dark Precision Lab Theme

A sophisticated dark interface inspired by professional image-processing tools.
Deep charcoal backgrounds, vivid teal accents, clean geometric lines.
"""

# -- Color Palette ------------------------------------------------
BG_DARKEST = "#131419"
BG_DARK = "#1a1b23"
BG_PANEL = "#22232d"
BG_INPUT = "#282935"
BG_HOVER = "#2e3040"
BG_PRESSED = "#353748"

ACCENT = "#00D4AA"
ACCENT_HOVER = "#00E8BB"
ACCENT_PRESSED = "#00B892"
ACCENT_DIM = "#00D4AA40"  # 25% opacity

DANGER = "#FF6B6B"
WARNING = "#F0A030"
SUCCESS = "#00D4AA"

TEXT_PRIMARY = "#E8E9ED"
TEXT_SECONDARY = "#8B8D98"
TEXT_MUTED = "#5C5E6A"
TEXT_ON_ACCENT = "#0A0F0D"

BORDER = "#2d2e3a"
BORDER_FOCUS = ACCENT
BORDER_SUBTLE = "#24252f"

SCROLLBAR_BG = BG_DARK
SCROLLBAR_HANDLE = "#3a3c4a"
SCROLLBAR_HOVER = "#4a4d5e"

# -- Drop Zone ----------------------------------------------------
DROP_ZONE_DEFAULT = f"""
    QLabel {{
        border: 2px dashed {TEXT_MUTED};
        border-radius: 16px;
        background: {BG_PANEL};
        color: {TEXT_SECONDARY};
        font-size: 17px;
        font-weight: 500;
        padding: 26px;
    }}
"""

DROP_ZONE_HOVER = f"""
    QLabel {{
        border: 2px dashed {ACCENT};
        border-radius: 16px;
        background: #1a2a28;
        color: {ACCENT};
        font-size: 17px;
        font-weight: 500;
        padding: 26px;
    }}
"""

DROP_ZONE_IMAGE = f"""
    QLabel {{
        border: 2px solid {BORDER};
        border-radius: 16px;
        background: {BG_PANEL};
        padding: 4px;
    }}
"""

# -- Global Application QSS --------------------------------------
APP_STYLESHEET = f"""

/* --- Base --- */
QMainWindow, QDialog {{
    background: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
    font-size: 17px;
}}

QWidget {{
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
}}

/* --- Toolbar --- */
QToolBar {{
    background: {BG_DARKEST};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 8px 16px;
    spacing: 10px;
}}

QToolBar QToolButton {{
    background: transparent;
    color: {TEXT_SECONDARY};
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 8px 21px;
    font-size: 17px;
    font-weight: 500;
}}
QToolBar QToolButton:hover {{
    background: {BG_HOVER};
    color: {TEXT_PRIMARY};
    border-color: {BORDER};
}}
QToolBar QToolButton:pressed {{
    background: {BG_PRESSED};
}}

/* --- Tabs --- */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 14px;
    background: {BG_DARK};
    margin-top: 14px;
}}
QTabWidget::tab-bar {{
    alignment: left;
    left: 12px;
}}
QTabBar {{
    background: {BG_PANEL};
    border: 1px solid {BORDER_SUBTLE};
    border-radius: 13px;
    padding: 5px;
}}
QTabBar::tab {{
    background: transparent;
    color: {TEXT_SECONDARY};
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 10px 24px;
    margin-right: 4px;
    min-width: 72px;
    font-size: 16px;
    font-weight: 700;
}}
QTabBar::tab:last {{
    margin-right: 0px;
}}
QTabBar::tab:hover {{
    background: {BG_HOVER};
    color: {TEXT_PRIMARY};
}}
QTabBar::tab:selected {{
    background: {ACCENT};
    color: {TEXT_ON_ACCENT};
    border-color: {ACCENT_HOVER};
}}
QTabBar::tab:selected:hover {{
    background: {ACCENT_HOVER};
}}
/* --- Section Labels --- */
QLabel#sectionLabel {{
    color: {TEXT_SECONDARY};
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 0px 5px 8px 5px;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 5px;
}}

/* --- Buttons --- */
QPushButton {{
    background: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 12px 26px;
    font-size: 17px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: {BG_HOVER};
    border-color: {TEXT_MUTED};
}}
QPushButton:pressed {{
    background: {BG_PRESSED};
}}
QPushButton:disabled {{
    background: {BG_PANEL};
    color: {TEXT_MUTED};
    border-color: {BORDER_SUBTLE};
}}

QPushButton#primaryBtn {{
    background: {ACCENT};
    color: {TEXT_ON_ACCENT};
    border: none;
    font-weight: 700;
    font-size: 18px;
    padding: 14px 31px;
}}
QPushButton#primaryBtn:hover {{
    background: {ACCENT_HOVER};
}}
QPushButton#primaryBtn:pressed {{
    background: {ACCENT_PRESSED};
}}
QPushButton#primaryBtn:disabled {{
    background: {TEXT_MUTED};
    color: {BG_DARK};
}}

QPushButton#successBtn {{
    background: transparent;
    color: {ACCENT};
    border: 1px solid {ACCENT};
}}
QPushButton#successBtn:hover {{
    background: {ACCENT};
    color: {TEXT_ON_ACCENT};
}}
QPushButton#successBtn:disabled {{
    color: {TEXT_MUTED};
    border-color: {BORDER};
    background: transparent;
}}

QPushButton#compactBtn {{
    padding: 8px 18px;
    font-size: 16px;
    font-weight: 600;
    border-radius: 8px;
}}

/* --- Line Edit --- */
QLineEdit {{
    background: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 17px;
    selection-background-color: {ACCENT_DIM};
}}
QLineEdit:focus {{
    border-color: {ACCENT};
}}
QLineEdit::placeholder {{
    color: {TEXT_MUTED};
}}

/* --- CheckBox --- */
QCheckBox {{
    color: {TEXT_SECONDARY};
    spacing: 8px;
    font-size: 15px;
}}
QCheckBox:checked {{
    color: {TEXT_PRIMARY};
}}

/* --- ComboBox --- */
QComboBox {{
    background: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 17px;
    min-height: 23px;
}}
QComboBox:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 36px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 8px solid {TEXT_SECONDARY};
    margin-right: 10px;
}}
QComboBox QAbstractItemView {{
    background: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 5px;
    selection-background-color: {BG_HOVER};
    selection-color: {ACCENT};
    outline: none;
}}

/* --- Text Edit --- */
QTextEdit {{
    background: {BG_DARKEST};
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER};
    border-radius: 13px;
    padding: 13px 18px;
    font-family: "Cascadia Code", "Consolas", "Microsoft YaHei UI", monospace;
    font-size: 16px;
    selection-background-color: {ACCENT_DIM};
}}
QTextEdit[readOnly="true"] {{
    background: {BG_DARKEST};
}}

/* --- Splitter --- */
QSplitter::handle {{
    background: {BORDER};
}}
QSplitter::handle:horizontal {{
    width: 2px;
    margin: 12px 8px;
}}
QSplitter::handle:vertical {{
    height: 2px;
    margin: 8px 12px;
}}
QSplitter::handle:hover {{
    background: {ACCENT};
}}

/* --- Status Bar --- */
QStatusBar {{
    background: {BG_DARKEST};
    color: {TEXT_MUTED};
    border-top: 1px solid {BORDER};
    font-size: 16px;
    padding: 5px 16px;
}}

/* --- Scrollbars --- */
QScrollBar:vertical {{
    background: {SCROLLBAR_BG};
    width: 10px;
    border-radius: 5px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {SCROLLBAR_HANDLE};
    border-radius: 5px;
    min-height: 39px;
}}
QScrollBar::handle:vertical:hover {{
    background: {SCROLLBAR_HOVER};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {SCROLLBAR_BG};
    height: 10px;
    border-radius: 5px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {SCROLLBAR_HANDLE};
    border-radius: 5px;
    min-width: 39px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {SCROLLBAR_HOVER};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* --- Message Box --- */
QMessageBox {{
    background: {BG_PANEL};
}}
QMessageBox QLabel {{
    color: {TEXT_PRIMARY};
    font-size: 17px;
}}
QMessageBox QPushButton {{
    min-width: 104px;
}}

/* --- Tooltips --- */
QToolTip {{
    background: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 13px;
    font-size: 16px;
}}

/* --- Context Menu --- */
QMenu {{
    background: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 8px;
    font-size: 17px;
}}
QMenu::item {{
    background: transparent;
    color: {TEXT_PRIMARY};
    padding: 10px 26px;
    border-radius: 8px;
    margin: 2px;
}}
QMenu::item:selected {{
    background: {BG_HOVER};
    color: {ACCENT};
}}
QMenu::item:disabled {{
    color: {TEXT_MUTED};
}}
QMenu::separator {{
    height: 1px;
    background: {BORDER};
    margin: 8px 13px;
}}
"""

