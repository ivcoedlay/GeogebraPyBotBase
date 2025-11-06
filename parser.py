import re
import logging
from sympy import symbols, Eq, sympify

logger = logging.getLogger(__name__)


def extract_equation_parts(eq_str):
    """Извлекает левую и правую части уравнения."""
    if '=' not in eq_str:
        raise ValueError("Уравнение должно содержать '='")
    left, right = eq_str.split('=', 1)
    left = left.strip()
    right = right.strip()
    if not left or not right:
        raise ValueError("Левая или правая часть уравнения пуста")
    return left, right


def get_parameters(expr_str):
    """Извлекает параметры из строки выражения."""
    letters = set(re.findall(r'[a-zA-Z]', expr_str))
    params = sorted([c for c in letters if c.lower() != 'x'])
    return params


def parse_equation(eq_str):
    """
    Парсит строку уравнения в объект sympy.Eq, переменную x и список параметров.
    """
    try:
        left, right = extract_equation_parts(eq_str)
        all_vars = set(re.findall(r'[a-zA-Z]', eq_str))
        # Создаем словарь символов, включая 'x'
        symbols_dict = {v: symbols(v) for v in all_vars}

        # Парсим левую и правую части отдельно
        lhs = sympify(left, locals=symbols_dict)
        rhs = sympify(right, locals=symbols_dict)

        # Создаем уравнение
        eq = Eq(lhs, rhs)

        # Получаем символ 'x' и параметры
        x = symbols_dict.get('x', symbols('x'))
        params = [symbols_dict[p] for p in get_parameters(eq_str)]

        logger.debug(f"Парсинг: уравнение={eq}, x={x}, params={params}")
        return eq, x, params
    except Exception as e:
        logger.error(f"Ошибка парсинга уравнения '{eq_str}': {e}", exc_info=True)
        raise ValueError(f"Ошибка парсинга: {e}")
