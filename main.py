import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QComboBox, QMessageBox, QFileDialog
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, pyqtSlot
from PyQt6.QtWebEngineCore import QWebEnginePage

from parser import get_parameters
from solver import solve_equation
from geogebra import generate_geogebra_js

EXAMPLES_FILE = "examples.json"
HTML_PATH = os.path.abspath("resources/geogebra.html")

class EquationSolverApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Решение уравнений с параметрами")
        self.resize(900, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # Переключатель режимов
        mode_layout = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Выберите режим", "Примеры", "Своё уравнение"])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_change)
        mode_layout.addWidget(QLabel("Режим:"))
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)

        # Примеры
        self.examples_combo = QComboBox()
        self.examples_combo.setVisible(False)
        self.examples_combo.currentTextChanged.connect(self.load_example)
        layout.addWidget(self.examples_combo)

        # Ввод уравнения
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Введите уравнение, например: a*x + b = 0")
        self.input_line.setVisible(False)
        layout.addWidget(self.input_line)

        # Кнопка решения
        self.solve_btn = QPushButton("Решить")
        self.solve_btn.clicked.connect(self.solve)
        self.solve_btn.setVisible(False)
        layout.addWidget(self.solve_btn)

        # Результат
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

        # GeoGebra
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl.fromLocalFile(HTML_PATH))
        layout.addWidget(self.web_view)

        # Сохранение
        self.save_btn = QPushButton("Сохранить результат")
        self.save_btn.clicked.connect(self.save_result)
        self.save_btn.setEnabled(False)
        layout.addWidget(self.save_btn)

        self.current_eq = ""
        self.current_steps = []
        self.current_js = ""

        self.load_examples()

    def load_examples(self):
        try:
            with open(EXAMPLES_FILE, 'r', encoding='utf-8') as f:
                self.examples_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить примеры: {e}")
            self.examples_data = {"linear": [], "quadratic": []}

    def on_mode_change(self, index):
        if index == 1:  # Примеры
            self.examples_combo.setVisible(True)
            self.input_line.setVisible(False)
            self.solve_btn.setVisible(False)
            items = []
            for i, ex in enumerate(self.examples_data["linear"], 1):
                items.append(f"Линейное {i}: {ex}")
            for i, ex in enumerate(self.examples_data["quadratic"], 1):
                items.append(f"Квадратное {i}: {ex}")
            self.examples_combo.clear()
            self.examples_combo.addItems(items)
        elif index == 2:  # Своё уравнение
            self.examples_combo.setVisible(False)
            self.input_line.setVisible(True)
            self.solve_btn.setVisible(True)
        else:
            self.examples_combo.setVisible(False)
            self.input_line.setVisible(False)
            self.solve_btn.setVisible(False)

    def load_example(self, text):
        if not text:
            return
        # Извлекаем уравнение из строки вида "Линейное 1: a*x + b = 0"
        if ':' in text:
            self.current_eq = text.split(':', 1)[1].strip()
            self.solve()

    def solve(self):
        if self.mode_combo.currentIndex() == 2:
            self.current_eq = self.input_line.text().strip()
        if not self.current_eq:
            return

        try:
            steps, x, params, expr = solve_equation(self.current_eq)
            self.current_steps = steps
            self.result_text.setPlainText("\n".join(steps))

            # Генерация GeoGebra JS
            js_code = generate_geogebra_js(expr, x, params)
            self.current_js = js_code

            # Загружаем JS после загрузки страницы
            self.web_view.loadFinished.connect(lambda ok: self.run_geogebra_js(js_code))
            self.web_view.setUrl(QUrl.fromLocalFile(HTML_PATH))

            self.save_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось решить уравнение:\n{e}")

    def run_geogebra_js(self, js_code):
        # Отключаем сигнал, чтобы не вызывать повторно
        self.web_view.loadFinished.disconnect()
        self.web_view.page().runJavaScript(f"setGeoGebraCode(`{js_code}`);")

    def save_result(self):
        if not self.current_eq:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить результат", "", "Text Files (*.txt)")
        if filename:
            if not filename.endswith(".txt"):
                filename += ".txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Уравнение: {self.current_eq}\n\n")
                f.write("Аналитическое решение:\n")
                f.write("\n".join(self.current_steps))
                f.write("\n\nGeoGebra JS-код:\n")
                f.write(self.current_js)
            QMessageBox.information(self, "Успех", "Результат сохранён!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EquationSolverApp()
    window.show()
    sys.exit(app.exec())