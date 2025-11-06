# geogebra.py

import logging
import re
from sympy import symbols

logger = logging.getLogger(__name__)

def get_function_expression_for_geogebra(expr, params):
    """
    Возвращает строку выражения f(x) для GeoGebra с подстановкой параметров.
    expr — это lhs - rhs (уже в виде sympy-выражения).
    """
    try:
        # Подстановка значений по умолчанию для параметров
        default_vals = {}
        for p in params:
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
                default_vals[p] = len(default_vals) + 1
        expr_num = expr.subs(default_vals)
        expr_num = expr_num.evalf()
        if expr_num.is_Float and expr_num == int(expr_num):
            expr_num = int(expr_num)
        s = str(expr_num).replace('**', '^')
        # Убираем * между числом и x: 2*x → 2x
        s = re.sub(r'(\d+)\s*\*\s*x', r'\1x', s)
        # Убираем пробелы и нормализуем
        s = s.replace(' ', '').replace('+', ' + ').replace('-', ' - ').strip()
        s = re.sub(r'\s+', ' ', s).replace(' + ', '+').replace(' - ', '-')
        if s.startswith('+'):
            s = s[1:]
        logger.debug(f"Выражение для GeoGebra: {s}")
        return s
    except Exception as e:
        logger.error(f"Ошибка в get_function_expression_for_geogebra: {e}", exc_info=True)
        return "0"

def generate_geogebra_url(func_str):
    """
    Генерирует URL для GeoGebra Graphing Calculator с заданным выражением.
    """
    # Кодируем выражение для безопасного использования в URL
    encoded_func = func_str.replace(' ', '%20').replace('+', '%2B').replace('-', '%2D').replace('*', '%2A').replace('/', '%2F')
    # Базовый URL для GeoGebra Graphing Calculator
    base_url = "https://www.geogebra.org/graphing"
    # Параметр для функции
    url = f"{base_url}?eq1={encoded_func}"
    logger.debug(f"Сгенерированный URL для GeoGebra: {url}")
    return url