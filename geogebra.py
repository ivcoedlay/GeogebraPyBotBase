import logging
from sympy import symbols

logger = logging.getLogger(__name__)

def generate_geogebra_js(expr, x, params):
    """
    Генерирует JavaScript-код для GeoGebra, подставляя числовые значения параметров.
    """
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
        # Убираем дробные части, если они .0
        expr_num = expr_num.evalf()
        if expr_num.is_Float and expr_num == int(expr_num):
            expr_num = int(expr_num)

        # Преобразование в строку для GeoGebra
        # Заменяем ** на ^ и сохраняем умножение между коэффициентом и переменной
        s = str(expr_num).replace('**', '^')
        # Заменяем умножение между коэффициентом и переменной (e.g., 1*x -> 1x)
        import re
        # Шаблон: число * переменная -> число переменная
        s = re.sub(r'(\d+)\s*\*\s*([a-zA-Z])', r'\1\2', s)
        # Шаблон: параметр * переменная -> параметр переменная (после подстановки)
        # Учитываем, что после подстановки это числа, так что предыдущая замена покрывает это
        s = s.replace('+ ', '+').replace('- ', '-').replace(' ', '')

        func_def = f'f(x) = {s}'
        # Команды для GeoGebra
        commands = [
            'Delete["f"]',  # Удаляем старую функцию
            'Delete["Roots"]', # Удаляем старые корни
            func_def,
            'Roots = Root[f]', # Находим корни
            'SetVisibleInView[f,1,true]', # Делаем f(x) видимой в виде 1 (график)
            'SetVisibleInView[Roots,1,true]', # Делаем Roots видимыми в виде 1
            'ShowAxes = true', # Показать оси
            'ZoomStandard[]' # Стандартный масштаб
        ]

        js_lines = [f'ggbApplet.evalCommand("{cmd}");' for cmd in commands]
        js_code = "\n".join(js_lines)

        full_js = f"""
        if (typeof ggbApplet !== 'undefined' && ggbApplet) {{
            console.log("[JS] Выполняем сгенерированный JS:");
            console.log(`{func_def}`);
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
