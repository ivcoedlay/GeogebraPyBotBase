import sys
import os
import json
import logging
import argparse
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QComboBox, QMessageBox, QFileDialog
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
from parser import get_parameters
from solver import solve_equation
from geogebra import get_function_expression_for_geogebra

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
        if not os.path.exists(HTML_PATH):
            logger.error(f"HTML-файл GeoGebra не найден: {HTML_PATH}")
            QMessageBox.critical(self, "Ошибка", f"Отсутствует файл: {HTML_PATH}")
        else:
            self.web_view.setUrl(QUrl.fromLocalFile(HTML_PATH))
        layout.addWidget(self.web_view)

        # Сохранение
        self.save_btn = QPushButton("Сохранить результат")
        self.save_btn.clicked.connect(self.save_result)
        self.save_btn.setEnabled(False)
        layout.addWidget(self.save_btn)

        self.current_eq = ""
        self.current_steps = []
        self.current_js = ""  # Теперь это строка выражения, не JS-код
        self.load_examples()

    def load_examples(self):
        try:
            with open(EXAMPLES_FILE, 'r', encoding='utf-8') as f:
                self.examples_data = json.load(f)
            logger.info("Примеры успешно загружены.")
        except Exception as e:
            logger.error(f"Не удалось загрузить примеры: {e}", exc_info=True)
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
        try:
            self.current_eq = text.split(':', 1)[1].strip()
            logger.info(f"Загружен пример: {self.current_eq}")
            self.solve()
        except Exception as e:
            logger.error(f"Ошибка при загрузке примера '{text}': {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить пример: {e}")

    def solve(self):
        if self.mode_combo.currentIndex() == 2:
            self.current_eq = self.input_line.text().strip()
        if not self.current_eq:
            logger.warning("Попытка решить пустое уравнение.")
            return
        logger.info(f"Решение уравнения: {self.current_eq}")
        try:
            steps, x, params, expr = solve_equation(self.current_eq)
            self.current_steps = steps
            self.result_text.setPlainText("\n".join(steps))
            func_str = get_function_expression_for_geogebra(expr, params)
            self.current_js = func_str
            try:
                self.web_view.loadFinished.disconnect()
            except TypeError:
                pass
            self.web_view.loadFinished.connect(lambda ok: self._on_web_loaded(ok, func_str))
            self.web_view.setUrl(QUrl.fromLocalFile(HTML_PATH))
            self.save_btn.setEnabled(True)
        except Exception as e:
            logger.error(f"Ошибка при решении уравнения: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Не удалось решить уравнение:\n{e}")

    def _on_web_loaded(self, ok, func_str):
        try:
            self.web_view.loadFinished.disconnect()
        except TypeError:
            pass
        if ok:
            self.update_geogebra_plot(func_str)

    def update_geogebra_plot(self, func_str):
        logger.debug(f"Обновление GeoGebra: f(x) = {func_str}")
        safe_str = func_str.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        self.web_view.page().runJavaScript(f"setFunctionExpression(`{safe_str}`);")

    def save_result(self):
        if not self.current_eq:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить результат", "", "Text Files (*.txt)")
        if filename:
            if not filename.endswith(".txt"):
                filename += ".txt"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Уравнение: {self.current_eq}\n")
                    f.write("Аналитическое решение:\n")
                    f.write("\n".join(self.current_steps))
                    f.write("\nGeoGebra expression:\n")
                    f.write(self.current_js)
                logger.info(f"Результат сохранён в {filename}")
                QMessageBox.information(self, "Успех", "Результат сохранён!")
            except Exception as e:
                logger.error(f"Ошибка сохранения: {e}", exc_info=True)
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{e}")

def cli_mode():
    parser = argparse.ArgumentParser(description="Решение линейных и квадратных уравнений с параметрами")
    parser.add_argument("--eq", type=str, help="Уравнение, например: 'a*x + b = 0'")
    parser.add_argument("--example", type=str, help="Ключ примера: linear/1, quadratic/2 и т.д.")
    args = parser.parse_args()
    if not args.eq and not args.example:
        print("Укажите --eq или --example")
        return
    try:
        if args.example:
            with open(EXAMPLES_FILE, 'r', encoding='utf-8') as f:
                examples = json.load(f)
            cat, idx = args.example.split('/')
            eq = examples[cat][int(idx) - 1]
        else:
            eq = args.eq
        logger.info(f"CLI: решение уравнения: {eq}")
        steps, x, params, expr = solve_equation(eq)
        print("\n".join(steps))
        print("\nGeoGebra expression:")
        print(get_function_expression_for_geogebra(expr, params))
    except Exception as e:
        logger.error(f"CLI ошибка: {e}", exc_info=True)
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli_mode()
    else:
        app = QApplication(sys.argv)
        window = EquationSolverApp()
        window.show()
        sys.exit(app.exec())