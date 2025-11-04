import logging
import sympy as sp
from sympy import Eq, expand, sqrt

logger = logging.getLogger(__name__)

def solve_linear(eq, x, params):
    expr = eq.lhs - eq.rhs
    expr = expand(expr)
    A = expr.coeff(x, 1)
    B = expr.subs(x, 0)
    steps = []
    logger.debug(f"Линейное: A={A}, B={B}")
    if A == 0:
        if B == 0:
            steps.append("Уравнение превращается в 0 = 0 → решений бесконечно много.")
        else:
            steps.append(f"Уравнение превращается в {B} = 0 → решений нет.")
    else:
        sol = -B / A
        steps.append(f"Коэффициент при x: A = {A}")
        steps.append(f"Свободный член: B = {B}")
        steps.append(f"Решение: x = -B / A = {sol}")
    return steps

def solve_quadratic(eq, x, params):
    expr = eq.lhs - eq.rhs
    expr = expand(expr)
    a = expr.coeff(x, 2)
    b = expr.coeff(x, 1)
    c = expr.subs(x, 0)
    steps = []
    logger.debug(f"Квадратное: a={a}, b={b}, c={c}")
    if a == 0:
        steps.append("Коэффициент a = 0 → уравнение вырождается в линейное.")
        lin_eq = Eq(b*x + c, 0)
        steps += solve_linear(lin_eq, x, params)
    else:
        D = b**2 - 4*a*c
        steps.append(f"Коэффициенты: a = {a}, b = {b}, c = {c}")
        steps.append(f"Дискриминант: D = b² - 4ac = {D}")
        if D == 0:
            x0 = -b / (2*a)
            steps.append(f"D = 0 → один корень: x = {x0}")
        elif D.is_number and D < 0:
            steps.append("D < 0 → действительных корней нет.")
        else:
            x1 = (-b + sqrt(D)) / (2*a)
            x2 = (-b - sqrt(D)) / (2*a)
            steps.append(f"Корни: x₁ = {x1}, x₂ = {x2}")
    return steps

def solve_equation(eq_str):
    from parser import parse_equation
    try:
        eq, x, params = parse_equation(eq_str)
    except Exception as e:
        raise ValueError(f"Ошибка парсинга: {e}")

    expr = eq.lhs - eq.rhs
    expr = sp.simplify(expr)

    try:
        degree = sp.degree(expr, x)
    except Exception:
        degree = -1

    logger.debug(f"Степень уравнения по x: {degree}")

    steps = []
    if degree == 1:
        steps = solve_linear(eq, x, params)
    elif degree == 2:
        steps = solve_quadratic(eq, x, params)
    elif degree == 0:
        if expr == 0:
            steps.append("Уравнение превращается в 0 = 0 → решений бесконечно много.")
        else:
            steps.append(f"Уравнение превращается в {expr} = 0 → решений нет.")
    else:
        steps.append("Поддерживаются только линейные и квадратные уравнения.")

    return steps, x, params, expr