import sys
import os
import json
import logging
import argparse
import sympy as sp
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QComboBox, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from parser import get_parameters, parse_equation
from solver import solve_equation

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
IMAGES_DIR = "images"


class MatplotlibWidget(QWidget):
    """Виджет для отображения графиков matplotlib"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def clear(self):
        """Очистка графика"""
        self.ax.clear()
        self.canvas.draw()

    def plot_function(self, func, x_range, roots=None, title=""):
        """Построение графика функции"""
        self.ax.clear()

        x = np.linspace(x_range[0], x_range[1], 1000)
        y = np.array([func(val) for val in x], dtype=float)

        # Убираем бесконечности и NaN
        mask = np.isfinite(y)
        x = x[mask]
        y = y[mask]

        if len(x) == 0:
            logger.warning("Все значения функции не являются конечными числами")
            self.ax.text(0.5, 0.5, "Невозможно построить график",
                         ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            return

        # Построение основного графика
        self.ax.plot(x, y, 'b-', linewidth=2, label='f(x)')

        # Добавление осей
        self.ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        self.ax.axvline(x=0, color='k', linestyle='-', alpha=0.3)

        # Отметка корней
        if roots and len(roots) > 0:
            valid_roots = []
            for root_val in roots:
                try:
                    if x_range[0] <= root_val <= x_range[1]:
                        valid_roots.append(root_val)
                        self.ax.plot(root_val, 0, 'ro', markersize=8, label=f'Корень: {root_val:.3f}')
                        self.ax.axvline(x=root_val, color='r', linestyle='--', alpha=0.5)
                except (TypeError, ValueError):
                    continue

        # Настройка графика
        self.ax.grid(True, alpha=0.3)
        self.ax.set_title(title)
        self.ax.set_xlabel('x')
        self.ax.set_ylabel('f(x)')

        # Убираем дублирующиеся метки в легенде
        handles, labels = self.ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        self.ax.legend(by_label.values(), by_label.keys())

        # Автоматическое масштабирование
        if len(y) > 0:
            y_min, y_max = np.min(y), np.max(y)
            margin = max(1, (y_max - y_min) * 0.1)
            self.ax.set_ylim(y_min - margin, y_max + margin)

        self.canvas.draw()

    def save_plot(self, filename):
        """Сохранение графика в файл"""
        self.figure.savefig(filename, bbox_inches='tight')
        logger.info(f"График сохранён в {filename}")


class EquationSolverApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Решение уравнений с параметрами")
        self.resize(900, 700)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # Создание папки для изображений, если её нет
        os.makedirs(IMAGES_DIR, exist_ok=True)

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

        # График
        self.plot_widget = MatplotlibWidget()
        layout.addWidget(self.plot_widget)

        # Кнопки для работы с графиком
        plot_btn_layout = QHBoxLayout()

        self.plot_btn = QPushButton("Построить график")
        self.plot_btn.clicked.connect(self.plot_graph)
        self.plot_btn.setEnabled(False)
        plot_btn_layout.addWidget(self.plot_btn)

        self.save_plot_btn = QPushButton("Сохранить график")
        self.save_plot_btn.clicked.connect(self.save_plot)
        self.save_plot_btn.setEnabled(False)
        plot_btn_layout.addWidget(self.save_plot_btn)

        layout.addLayout(plot_btn_layout)

        # Сохранение результата
        self.save_btn = QPushButton("Сохранить результат")
        self.save_btn.clicked.connect(self.save_result)
        self.save_btn.setEnabled(False)
        layout.addWidget(self.save_btn)

        self.current_eq = ""
        self.current_steps = []
        self.current_roots = []
        self.current_expr = None
        self.current_x = None
        self.current_params = []
        self.current_example_name = ""

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
            self.plot_btn.setEnabled(False)
            self.save_plot_btn.setEnabled(False)

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
            self.plot_btn.setEnabled(False)
            self.save_plot_btn.setEnabled(False)

        else:
            self.examples_combo.setVisible(False)
            self.input_line.setVisible(False)
            self.solve_btn.setVisible(False)
            self.plot_btn.setEnabled(False)
            self.save_plot_btn.setEnabled(False)

    def load_example(self, text):
        if not text:
            return
        try:
            parts = text.split(':', 1)
            self.current_example_name = parts[0].strip()
            self.current_eq = parts[1].strip()
            logger.info(f"Загружен пример: {self.current_eq}")
            self.solve()
        except Exception as e:
            logger.error(f"Ошибка при загрузке примера '{text}': {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить пример: {e}")

    def solve(self):
        if self.mode_combo.currentIndex() == 2:
            self.current_eq = self.input_line.text().strip()
            self.current_example_name = ""

        if not self.current_eq:
            logger.warning("Попытка решить пустое уравнение.")
            return

        logger.info(f"Решение уравнения: {self.current_eq}")
        try:
            # Изменено: теперь функция solve_equation возвращает корни
            steps, x, params, expr, roots = solve_equation(self.current_eq)
            self.current_steps = steps
            self.current_x = x
            self.current_params = params
            self.current_expr = expr
            self.current_roots = roots

            self.result_text.setPlainText("\n".join(steps))
            self.save_btn.setEnabled(True)

            # Разрешаем построение графика после решения
            self.plot_btn.setEnabled(True)

        except Exception as e:
            logger.error(f"Ошибка при решении уравнения: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Не удалось решить уравнение:\n{e}")

    def get_default_param_values(self):
        """Возвращает значения по умолчанию для параметров"""
        default_vals = {}
        for p in self.current_params:
            name = str(p)
            if name == 'a':
                default_vals[p] = 1
            elif name == 'b':
                default_vals[p] = -2
            elif name == 'c':
                default_vals[p] = 1
            elif name == 'p':
                default_vals[p] = 2
            else:
                # Используем значения 1, 2, 3... для остальных параметров
                default_vals[p] = list(default_vals.values()).count(0) + 1

        return default_vals

    def plot_graph(self):
        if not self.current_expr or not self.current_x:
            QMessageBox.warning(self, "Ошибка", "Сначала решите уравнение")
            return

        try:
            # Получаем значения по умолчанию для параметров
            default_vals = self.get_default_param_values()

            # Подставляем значения в выражение
            expr_num = self.current_expr.subs(default_vals)
            logger.debug(f"Выражение с подставленными значениями: {expr_num}")

            # Подставляем значения в корни
            numeric_roots = []
            for root in self.current_roots:
                try:
                    num_root = root.subs(default_vals)
                    num_root = sp.N(num_root)  # Численное значение
                    if num_root.is_real:
                        numeric_roots.append(float(num_root))
                        logger.debug(f"Числовой корень: {float(num_root)}")
                except Exception as e:
                    logger.warning(f"Не удалось вычислить числовой корень: {e}")

            # Создание функции для построения графика
            expr_func = sp.lambdify(self.current_x, expr_num, 'numpy')

            # Определение диапазона для построения
            x_range = self.get_plot_range(numeric_roots)

            # Построение графика
            title = f"График: {self.current_eq}"
            if default_vals:
                params_str = ", ".join([f"{str(k)}={v}" for k, v in default_vals.items()])
                title += f"\n(Параметры: {params_str})"

            self.plot_widget.plot_function(expr_func, x_range, numeric_roots, title)

            # Активируем кнопку сохранения графика
            self.save_plot_btn.setEnabled(True)

        except Exception as e:
            logger.error(f"Ошибка при построении графика: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Не удалось построить график:\n{e}")
            self.plot_widget.clear()

    def get_plot_range(self, roots=None):
        """Определение подходящего диапазона для построения графика"""
        # Базовый диапазон
        base_range = [-10, 10]

        # Если есть корни, расширяем диапазон, чтобы включить их все
        if roots and len(roots) > 0:
            min_root = min(roots)
            max_root = max(roots)

            # Расширяем диапазон с запасом
            margin = max(5, (max_root - min_root) * 0.5)
            return [min_root - margin, max_root + margin]

        # Для квадратных уравнений находим вершину параболы
        try:
            # Проверяем, является ли уравнение квадратным
            expr = sp.expand(self.current_expr)
            if expr.as_poly().degree() == 2:
                a = expr.as_poly().coeff_monomial(self.current_x ** 2)
                b = expr.as_poly().coeff_monomial(self.current_x)
                if not sp.simplify(a) == 0:
                    vertex_x = -b / (2 * a)
                    vertex_x = float(vertex_x.subs(self.get_default_param_values()))
                    return [vertex_x - 10, vertex_x + 10]
        except Exception as e:
            logger.warning(f"Не удалось определить вершину параболы: {e}")

        return base_range

    def save_plot(self):
        """Сохранение графика в файл"""
        if not self.current_eq:
            QMessageBox.warning(self, "Ошибка", "Нет графика для сохранения")
            return

        try:
            # Генерация имени файла
            if self.current_example_name:
                base_name = self.current_example_name.replace(" ", "_").lower()
            else:
                # Создаем осмысленное имя из уравнения
                base_name = self.current_eq.replace(" ", "_").replace("=", "_eq_")
                base_name = "".join(c for c in base_name if c.isalnum() or c in ['_', '-', '.'])
                base_name = base_name[:50]  # Ограничиваем длину

            # Добавляем суффикс, если файл уже существует
            filename = os.path.join(IMAGES_DIR, f"{base_name}.png")
            counter = 1
            while os.path.exists(filename):
                filename = os.path.join(IMAGES_DIR, f"{base_name}_{counter}.png")
                counter += 1

            self.plot_widget.save_plot(filename)
            QMessageBox.information(self, "Успех", f"График сохранён в:\n{filename}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении графика: {e}", exc_info=True)
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить график:\n{e}")

    def save_result(self):
        """Сохранение аналитического решения"""
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
        steps, x, params, expr, roots = solve_equation(eq)
        print("\n".join(steps))

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