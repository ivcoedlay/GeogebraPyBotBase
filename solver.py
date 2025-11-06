import logging
import sympy as sp
from sympy import Eq, expand, sqrt

logger = logging.getLogger(__name__)

def solve_linear(eq, x, params):
    """Решает линейное уравнение."""
    expr = eq.lhs - eq.rhs
    expr = expand(expr)
    A = expr.coeff(x, 1)
    B = expr.subs(x, 0)

    steps = []
    logger.debug(f"Линейное: A={A}, B={B}")

    # Проверяем, является ли A нулем
    if A.is_zero:
        if B.is_zero:
            steps.append("Уравнение превращается в 0 = 0 → решений бесконечно много.")
        else:
            steps.append(f"Уравнение превращается в {B} = 0 → решений нет.")
    else:
        sol = -B / A
        steps.append(f"Коэффициент при x: A = {A}")
        steps.append(f"Свободный член: B = {B}")
        steps.append(f"Решение: x = -B / A = {sp.simplify(sol)}")

    return steps

def solve_quadratic(eq, x, params):
    """Решает квадратное уравнение."""
    expr = eq.lhs - eq.rhs
    expr = expand(expr)
    a = expr.coeff(x, 2)
    b = expr.coeff(x, 1)
    c = expr.subs(x, 0)

    steps = []
    logger.debug(f"Квадратное: a={a}, b={b}, c={c}")

    # Проверяем, является ли a нулем (уравнение линейное)
    if a.is_zero:
        steps.append("Коэффициент a = 0 → уравнение вырождается в линейное.")
        lin_eq = Eq(b*x + c, 0)
        steps += solve_linear(lin_eq, x, params)
    else:
        D = b**2 - 4*a*c
        steps.append(f"Коэффициенты: a = {a}, b = {b}, c = {c}")
        steps.append(f"Дискриминант: D = b² - 4ac = {D}")

        # Проверяем, является ли D нулем
        if D.is_zero:
            x0 = -b / (2*a)
            steps.append(f"D = 0 → один корень: x = {sp.simplify(x0)}")
        # Проверяем, является ли D отрицательным числом
        elif D.is_number and D < 0:
            steps.append("D < 0 → действительных корней нет.")
        else:
            x1 = (-b + sqrt(D)) / (2*a)
            x2 = (-b - sqrt(D)) / (2*a)
            steps.append(f"Корни: x₁ = {sp.simplify(x1)}, x₂ = {sp.simplify(x2)}")

    return steps

def solve_equation(eq_str):
    """Основная функция решения уравнения."""
    from parser import parse_equation
    try:
        eq, x, params = parse_equation(eq_str)
    except Exception as e:
        raise ValueError(f"Ошибка парсинга: {e}")

    # Теперь eq гарантированно является Eq(lhs, rhs)
    expr = eq.lhs - eq.rhs

    # Не используем sp.simplify, так как он может изменить вид выражения
    # expr = sp.simplify(expr)

    try:
        degree = sp.degree(expr, x)
    except Exception:
        degree = -1 # Если степень не может быть определена

    logger.debug(f"Степень уравнения по x: {degree}")

    steps = []
    if degree == 1:
        steps = solve_linear(eq, x, params)
    elif degree == 2:
        steps = solve_quadratic(eq, x, params)
    elif degree == 0:
        # Постоянный член
        constant_term = expr
        if constant_term.is_zero:
            steps.append("Уравнение превращается в 0 = 0 → решений бесконечно много.")
        else:
            steps.append(f"Уравнение превращается в {constant_term} = 0 → решений нет.")
    else:
        steps.append("Поддерживаются только линейные и квадратные уравнения.")
    return steps, x, params, expr
