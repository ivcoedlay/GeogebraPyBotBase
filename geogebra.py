import json

def generate_geogebra_js(expr, x, params):
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
    return js_code.strip()