import logging
from sympy import symbols

logger = logging.getLogger(__name__)

def generate_geogebra_js(expr, x, params):
    try:
        # Подстановка числовых значений вместо символьных параметров
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
                # Используем 1, 2, 3... для остальных
                default_vals[p] = len(default_vals) + 1

        expr_num = expr.subs(default_vals)
        expr_num = expr_num.evalf()

        # Преобразование в строку для GeoGebra
        s = str(expr_num).replace('**', '^').replace('*', '')
        s = s.replace('+ ', '+').replace('- ', '-')

        func_def = f'f(x) = {s}'

        # Без фигурных скобок — они ломают команду
        commands = [
            'Delete["f"]',
            'Delete["Roots"]',
            func_def,
            'Roots = Root[f]',
            'ShowAxes = true',
            'ZoomStandard[]'
        ]

        js_lines = [f'ggbApplet.evalCommand("{cmd}");' for cmd in commands]
        js_code = "\n".join(js_lines)

        full_js = f"""
        if (typeof ggbApplet !== 'undefined' && ggbApplet) {{
            {js_code}
        }} else {{
            console.log("[JS fallback] ggbApplet недоступен при генерации.");
        }}
        """

        logger.debug(f"Сгенерирован GeoGebra JS (с подстановкой): {func_def}")
        return full_js.strip()

    except Exception as e:
        logger.error(f"Ошибка в generate_geogebra_js: {e}", exc_info=True)
        return "// Ошибка генерации GeoGebra JS"