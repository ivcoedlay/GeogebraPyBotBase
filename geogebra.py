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
        if 'x' not in s:
            # Константное уравнение: f(x) = const
            pass
        logger.debug(f"Выражение для GeoGebra: {s}")
        return s
    except Exception as e:
        logger.error(f"Ошибка в get_function_expression_for_geogebra: {e}", exc_info=True)
        return "0"