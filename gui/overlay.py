import os
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS_DIR = os.path.join(BASE_DIR, "icons")


def load_svg_small(filename, color="#484f58", size=14):
    path = os.path.join(ICONS_DIR, filename)
    if not os.path.exists(path):
        return QPixmap()
    renderer = QSvgRenderer(path)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), color)
    painter.end()
    return pixmap


class Overlay(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.drag_pos = None
        self.label_widgets = {}

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(220, 260)
        self.move(50, 50)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: rgba(13, 17, 23, 235);
                border-radius: 14px;
                border: 1px solid rgba(48, 54, 61, 0.6);
            }
        """)
        clayout = QVBoxLayout(container)
        clayout.setContentsMargins(14, 12, 14, 12)
        clayout.setSpacing(4)

        master_row = QHBoxLayout()
        self.master_dot = QLabel()
        self.master_dot.setFixedSize(10, 10)
        self.master_dot.setStyleSheet("background: #7ee787; border-radius: 5px;")
        master_row.addWidget(self.master_dot)
        self.master_label = QLabel("АКТИВЕН [F7]")
        self.master_label.setStyleSheet("color: #7ee787; font-weight: bold; font-size: 12px; background: transparent;")
        master_row.addWidget(self.master_label)
        master_row.addStretch()
        clayout.addLayout(master_row)

        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #21262d;")
        clayout.addWidget(sep)

        modes = [
            ("left", "left.svg", "U", "ЛКМ"),
            ("right", "right.svg", "I", "ПКМ"),
            ("jump", "jump.svg", "X", "Jump"),
            ("dig", "dig.svg", "Y", "Копание"),
            ("run", "run.svg", "Ё", "Бег"),
            ("build", "build.svg", "F6", "Стройка"),
        ]
        for mode, icon_file, key, name in modes:
            row = QHBoxLayout()
            icon_lbl = QLabel()
            icon_lbl.setPixmap(load_svg_small(icon_file, "#484f58"))
            icon_lbl.setStyleSheet("background: transparent;")
            row.addWidget(icon_lbl)
            txt = QLabel(f"[{key}] {name}")
            txt.setStyleSheet("color: #484f58; font-size: 11px; background: transparent;")
            row.addWidget(txt)
            row.addStretch()
            clayout.addLayout(row)
            self.label_widgets[mode] = (icon_lbl, txt, icon_file)

        self.timer_label = QLabel("")
        self.timer_label.setStyleSheet("color: #f0883e; font-weight: bold; padding-top: 4px; font-size: 12px; background: transparent;")
        clayout.addWidget(self.timer_label)

        layout.addWidget(container)

        self.backend.state_changed.connect(self.on_state_changed)
        self.backend.master_changed.connect(self.on_master_changed)
        self.backend.timer_updated.connect(self.timer_label.setText)

    @Slot(str, bool)
    def on_state_changed(self, mode, is_on):
        if mode in self.label_widgets:
            icon_lbl, txt, icon_file = self.label_widgets[mode]
            color = "#7ee787" if is_on else "#484f58"
            icon_lbl.setPixmap(load_svg_small(icon_file, color))
            txt.setStyleSheet(f"color: {color}; font-size: 11px; background: transparent;")

    @Slot(bool)
    def on_master_changed(self, is_on):
        if is_on:
            self.master_label.setText("АКТИВЕН [F7]")
            self.master_label.setStyleSheet("color: #7ee787; font-weight: bold; font-size: 12px; background: transparent;")
            self.master_dot.setStyleSheet("background: #7ee787; border-radius: 5px;")
        else:
            self.master_label.setText("ОСТАНОВЛЕН [F7]")
            self.master_label.setStyleSheet("color: #f85149; font-weight: bold; font-size: 12px; background: transparent;")
            self.master_dot.setStyleSheet("background: #f85149; border-radius: 5px;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None
        event.accept()