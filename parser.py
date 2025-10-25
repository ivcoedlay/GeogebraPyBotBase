import re
from sympy import symbols, Eq, parse_expr

def extract_equation_parts(eq_str):
    if '=' not in eq_str:
        raise ValueError("Уравнение должно содержать '='")
    left, right = eq_str.split('=', 1)
    return left.strip(), right.strip()

def get_parameters(expr_str):
    # Все латинские буквы, кроме 'x'
    letters = set(re.findall(r'[a-zA-Z]', expr_str))
    params = sorted([c for c in letters if c.lower() != 'x'])
    return params

def parse_equation(eq_str):
    left, right = extract_equation_parts(eq_str)
    all_vars = set(re.findall(r'[a-zA-Z]', eq_str))
    symbols_dict = {v: symbols(v) for v in all_vars}
    lhs = parse_expr(left, symbols_dict, evaluate=False)
    rhs = parse_expr(right, symbols_dict, evaluate=False)
    eq = Eq(lhs, rhs)
    x = symbols_dict.get('x', symbols('x'))
    params = [symbols_dict[p] for p in get_parameters(eq_str)]
    return eq, x, params