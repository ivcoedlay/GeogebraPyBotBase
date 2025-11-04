import logging

logger = logging.getLogger(__name__)

def generate_geogebra_js(expr, x, params):
    try:
        def to_geogebra_expr(expr):
            s = str(expr).replace('**', '^')
            s = s.replace('*', '')
            s = s.replace('+ ', '+')
            s = s.replace('- ', '-')
            return s

        expr_str = to_geogebra_expr(expr)
        func_def = f"f(x) = {expr_str}"
        js_code = f"""
        if (typeof ggbApplet !== 'undefined') {{
            ggbApplet.evalCommand("{func_def}");
            ggbApplet.evalCommand("Roots = {{Root[f]}}");
            ggbApplet.evalCommand("ShowAxes = true");
            ggbApplet.evalCommand("ZoomIn(1)");
        }} else {{
            console.log("GeoGebra ещё не готов.");
        }}
        """
        logger.debug(f"Сгенерирован GeoGebra JS: {func_def}")
        return js_code.strip()
    except Exception as e:
        logger.error(f"Ошибка генерации GeoGebra JS: {e}", exc_info=True)
        return "// Ошибка генерации GeoGebra JS"