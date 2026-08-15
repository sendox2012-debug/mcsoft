import os
from datetime import datetime

from PySide6.QtCore import Qt, Slot, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QBrush
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QPushButton, QScrollArea, QSpinBox,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS_DIR = os.path.join(BASE_DIR, "icons")

MODE_INFO = [
    ("left", "ЛКМ автокликер", "left.svg", "U"),
    ("right", "ПКМ автокликер", "right.svg", "I"),
    ("jump", "Jump + Click", "jump.svg", "X"),
    ("dig", "Авто-копание", "dig.svg", "Y"),
    ("run", "Автобег", "run.svg", "Ё"),
    ("build", "Автостройка", "build.svg", "F6"),
]

HOTKEY_INFO = [
    ("master", "Мастер вкл/выкл"),
    ("left", "ЛКМ автокликер"),
    ("right", "ПКМ автокликер"),
    ("jump", "Jump + Click"),
    ("dig", "Авто-копание"),
    ("run", "Автобег"),
    ("build", "Автостройка"),
]


def load_svg(filename, color="#8b949e", size=22):
    path = os.path.join(ICONS_DIR, filename)
    if not os.path.exists(path):
        return QPixmap()
    renderer = QSvgRenderer(path)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    if color:
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(color))
        painter.end()
    return pixmap


def make_mode_icon(filename):
    icon = QIcon()
    icon.addPixmap(load_svg(filename, "#8b949e"), QIcon.Normal, QIcon.Off)
    icon.addPixmap(load_svg(filename, "#ffffff"), QIcon.Normal, QIcon.On)
    icon.addPixmap(load_svg(filename, "#c9d1d9"), QIcon.Active, QIcon.Off)
    icon.addPixmap(load_svg(filename, "#ffffff"), QIcon.Active, QIcon.On)
    return icon


class MainWindow(QMainWindow):
    def __init__(self, backend, config):
        super().__init__()
        self.backend = backend
        self.cfg = config
        self.mode_buttons = {}
        self.hotkey_inputs = {}

        self.setWindowTitle("MCSoft")
        self.setMinimumSize(540, 780)
        self.resize(540, 800)

        self._apply_styles()
        self._build_ui()
        self._connect_signals()

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background: #0d1117; }
            QWidget {
                background: transparent;
                color: #e6edf3;
                font-family: 'Segoe UI', 'Ubuntu', 'Noto Sans', sans-serif;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid #21262d;
                border-radius: 12px;
                background: #161b22;
            }
            QTabBar::tab {
                background: transparent;
                color: #8b949e;
                padding: 12px 22px;
                border: none;
                border-bottom: 2px solid transparent;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                color: #58a6ff;
                border-bottom: 2px solid #58a6ff;
            }
            QTabBar::tab:hover { color: #c9d1d9; }
            QGroupBox {
                color: #58a6ff;
                border: 1px solid #21262d;
                border-radius: 12px;
                margin-top: 16px;
                padding: 18px 14px 14px 14px;
                font-weight: 600;
                background: #161b22;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                background: #161b22;
            }
            QPushButton {
                background: #21262d;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 10px;
                padding: 12px 16px;
                text-align: left;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #30363d;
                border-color: #58a6ff;
            }
            QPushButton:checked {
                background: #238636;
                border-color: #2ea043;
                color: #ffffff;
            }
            QPushButton:pressed { background: #1f6feb; }
            QSpinBox, QLineEdit {
                background: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 8px 12px;
                selection-background-color: #1f6feb;
            }
            QSpinBox:focus, QLineEdit:focus { border-color: #58a6ff; }
            QCheckBox { spacing: 10px; font-weight: 500; }
            QCheckBox::indicator {
                width: 20px; height: 20px;
                border-radius: 6px;
                border: 2px solid #30363d;
                background: #0d1117;
            }
            QCheckBox::indicator:checked {
                background: #238636;
                border-color: #2ea043;
            }
            QTextEdit {
                background: #010409;
                color: #7ee787;
                border: 1px solid #21262d;
                border-radius: 10px;
                font-family: 'JetBrains Mono', Consolas, monospace;
                font-size: 11px;
                padding: 10px;
            }
            QScrollArea { border: none; }
        """)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet("background: #0d1117;")
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 12)

        header = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(load_svg("../icon.svg", None, 42) if os.path.exists(os.path.join(ICONS_DIR, "../icon.svg")) else QPixmap())
        icon_path = os.path.join(BASE_DIR, "icon.svg")
        if os.path.exists(icon_path):
            renderer = QSvgRenderer(icon_path)
            pm = QPixmap(42, 42)
            pm.fill(Qt.transparent)
            p = QPainter(pm)
            renderer.render(p)
            p.end()
            logo.setPixmap(pm)
        logo.setStyleSheet("background: transparent;")
        header.addWidget(logo)

        title = QLabel("MCSoft")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: #58a6ff; background: transparent;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.master_btn = QPushButton("  СКРИПТ АКТИВЕН")
        self.master_btn.setFixedHeight(50)
        self.master_btn.setCursor(Qt.PointingHandCursor)
        power_icon = QIcon()
        power_icon.addPixmap(load_svg("power.svg", "#ffffff"), QIcon.Normal, QIcon.Off)
        self.master_btn.setIcon(power_icon)
        self.master_btn.setIconSize(QSize(22, 22))
        self.master_btn.setStyleSheet("""
            QPushButton {
                background: #238636;
                border: 1px solid #2ea043;
                text-align: center;
                font-weight: bold;
                font-size: 15px;
                border-radius: 12px;
                color: #ffffff;
            }
            QPushButton:hover { background: #2ea043; }
        """)
        self.master_btn.clicked.connect(self.backend.toggle_master)
        layout.addWidget(self.master_btn)

        tabs = QTabWidget()
        tabs.addTab(self._build_modes_tab(), "Режимы")
        tabs.addTab(self._build_settings_tab(), "Настройки")
        tabs.addTab(self._build_hotkeys_tab(), "Клавиши")
        layout.addWidget(tabs)

        timer_row = QHBoxLayout()
        timer_icon_lbl = QLabel()
        timer_icon_lbl.setPixmap(load_svg("timer.svg", "#f0883e", 18))
        timer_icon_lbl.setStyleSheet("background: transparent;")
        timer_row.addWidget(timer_icon_lbl)
        self.timer_label = QLabel("")
        self.timer_label.setStyleSheet("color: #f0883e; font-size: 15px; font-weight: bold; background: transparent;")
        timer_row.addWidget(self.timer_label)
        timer_row.addStretch()
        layout.addLayout(timer_row)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(110)
        layout.addWidget(self.log_box)

        footer = QLabel("by @tg_sendo")
        footer.setStyleSheet("color: #484f58; font-size: 11px; background: transparent;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

    def _build_modes_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        for mode, label, icon_file, default_key in MODE_INFO:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: #161b22;
                    border: 1px solid #21262d;
                    border-radius: 12px;
                }
                QFrame:hover { border-color: #30363d; }
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(14, 10, 14, 10)

            btn = QPushButton(f"[{default_key}] {label}")
            btn.setCheckable(True)
            btn.setFixedHeight(46)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIcon(make_mode_icon(icon_file))
            btn.setIconSize(QSize(22, 22))
            btn.setStyleSheet("""
                QPushButton {
                    background: #21262d;
                    border: 1px solid #30363d;
                    border-radius: 10px;
                    padding: 10px 14px;
                    text-align: left;
                    font-weight: 500;
                }
                QPushButton:hover { background: #30363d; border-color: #58a6ff; }
                QPushButton:checked { background: #238636; border-color: #2ea043; color: #fff; }
            """)
            btn.clicked.connect(lambda checked, m=mode: self.backend.toggle(m))
            card_layout.addWidget(btn)
            layout.addWidget(card)
            self.mode_buttons[mode] = btn

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    def _build_settings_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        g1 = QGroupBox("КЛИКЕР")
        grid1 = QGridLayout(g1)
        grid1.addWidget(QLabel("CPS задержка:"), 0, 0)
        self.cps_spin = QSpinBox()
        self.cps_spin.setRange(10, 1000)
        self.cps_spin.setValue(int(self.cfg.get("cps_delay", 0.1) * 1000))
        self.cps_spin.setSuffix(" мс")
        self.cps_spin.valueChanged.connect(self._on_cps_changed)
        grid1.addWidget(self.cps_spin, 0, 1)
        layout.addWidget(g1)

        g2 = QGroupBox("JUMP / АВТОСТРОЙКА")
        grid2 = QGridLayout(g2)
        grid2.addWidget(QLabel("Тик прыжка:"), 0, 0)
        self.jump_tick_spin = QSpinBox()
        self.jump_tick_spin.setRange(10, 500)
        self.jump_tick_spin.setValue(int(self.cfg.get("jump_tick", 0.05) * 1000))
        self.jump_tick_spin.setSuffix(" мс")
        self.jump_tick_spin.valueChanged.connect(self._on_jump_tick_changed)
        grid2.addWidget(self.jump_tick_spin, 0, 1)
        grid2.addWidget(QLabel("Задержка стройки:"), 1, 0)
        self.build_spin = QSpinBox()
        self.build_spin.setRange(10, 1000)
        self.build_spin.setValue(int(self.cfg.get("build_delay", 0.05) * 1000))
        self.build_spin.setSuffix(" мс")
        self.build_spin.valueChanged.connect(self._on_build_changed)
        grid2.addWidget(self.build_spin, 1, 1)
        layout.addWidget(g2)

        g3 = QGroupBox("ОТДЫХ ПКМ")
        grid3 = QGridLayout(g3)
        grid3.addWidget(QLabel("Работа до отдыха:"), 0, 0)
        self.rest_int_spin = QSpinBox()
        self.rest_int_spin.setRange(1, 7200)
        self.rest_int_spin.setValue(self.cfg.get("rest_interval", 60))
        self.rest_int_spin.setSuffix(" сек")
        self.rest_int_spin.valueChanged.connect(self._on_rest_int_changed)
        grid3.addWidget(self.rest_int_spin, 0, 1)
        grid3.addWidget(QLabel("Длительность отдыха:"), 1, 0)
        self.rest_dur_spin = QSpinBox()
        self.rest_dur_spin.setRange(1, 3600)
        self.rest_dur_spin.setValue(self.cfg.get("rest_duration", 10))
        self.rest_dur_spin.setSuffix(" сек")
        self.rest_dur_spin.valueChanged.connect(self._on_rest_dur_changed)
        grid3.addWidget(self.rest_dur_spin, 1, 1)
        self.f12_check = QCheckBox("Нажимать F12 перед отдыхом")
        self.f12_check.setChecked(self.cfg.get("f12_before_rest", True))
        self.f12_check.toggled.connect(self._on_f12_toggled)
        grid3.addWidget(self.f12_check, 2, 0, 1, 2)
        layout.addWidget(g3)

        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    def _build_hotkeys_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        group = QGroupBox("НАЗНАЧЕНИЕ КЛАВИШ")
        grid = QGridLayout(group)

        hk = self.cfg.get("hotkeys", {})
        for i, (mode, label) in enumerate(HOTKEY_INFO):
            lbl = QLabel(label)
            inp = QLineEdit()
            inp.setText(str(hk.get(mode, "")))
            inp.setPlaceholderText("Клавиша...")
            inp.setFixedWidth(140)
            inp.textChanged.connect(lambda text, m=mode: self._update_hotkey(m, text))
            grid.addWidget(lbl, i, 0)
            grid.addWidget(inp, i, 1)
            self.hotkey_inputs[mode] = inp

        hint = QLabel("Доступно: A-Z, F1-F12, GRAVE (Ё)")
        hint.setStyleSheet("color: #8b949e; font-size: 11px;")
        grid.addWidget(hint, len(HOTKEY_INFO), 0, 1, 2)

        layout.addWidget(group)
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll

    def _on_cps_changed(self, value):
        self.cfg["cps_delay"] = value / 1000.0

    def _on_jump_tick_changed(self, value):
        self.cfg["jump_tick"] = value / 1000.0

    def _on_build_changed(self, value):
        self.cfg["build_delay"] = value / 1000.0

    def _on_rest_int_changed(self, value):
        self.cfg["rest_interval"] = value

    def _on_rest_dur_changed(self, value):
        self.cfg["rest_duration"] = value

    def _on_f12_toggled(self, checked):
        self.cfg["f12_before_rest"] = checked

    def _update_hotkey(self, mode, text):
        if "hotkeys" not in self.cfg:
            self.cfg["hotkeys"] = {}
        self.cfg["hotkeys"][mode] = text.strip()
        if mode in self.mode_buttons and mode != "master":
            for m, label, icon_file, _ in MODE_INFO:
                if m == mode:
                    self.mode_buttons[mode].setText(f"[{text.strip()}] {label}")
                    break

    def _connect_signals(self):
        self.backend.state_changed.connect(self.on_state_changed)
        self.backend.timer_updated.connect(self.timer_label.setText)
        self.backend.master_changed.connect(self.on_master_changed)
        self.backend.log_message.connect(self.on_log)

    @Slot(str, bool)
    def on_state_changed(self, mode, is_on):
        if mode in self.mode_buttons:
            self.mode_buttons[mode].setChecked(is_on)

    @Slot(bool)
    def on_master_changed(self, is_on):
        if is_on:
            self.master_btn.setText("  СКРИПТ АКТИВЕН")
            self.master_btn.setStyleSheet("""
                QPushButton {
                    background: #238636; border: 1px solid #2ea043;
                    text-align: center; font-weight: bold; font-size: 15px;
                    border-radius: 12px; color: #ffffff;
                }
                QPushButton:hover { background: #2ea043; }
            """)
        else:
            self.master_btn.setText("  СКРИПТ ОСТАНОВЛЕН")
            self.master_btn.setStyleSheet("""
                QPushButton {
                    background: #da3633; border: 1px solid #f85149;
                    text-align: center; font-weight: bold; font-size: 15px;
                    border-radius: 12px; color: #ffffff;
                }
                QPushButton:hover { background: #f85149; }
            """)

    @Slot(str)
    def on_log(self, msg):
        t = datetime.now().strftime("%H:%M:%S")
        self.log_box.append(f"[{t}] {msg}")

    def closeEvent(self, event):
        self.backend.stop()
        event.accept()