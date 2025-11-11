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
    roots = []

    logger.debug(f"Линейное: A={A}, B={B}")

    # Проверяем, является ли A нулем
    if sp.simplify(A) == 0:
        if sp.simplify(B) == 0:
            steps.append("Уравнение превращается в 0 = 0 → решений бесконечно много.")
        else:
            steps.append(f"Уравнение превращается в {B} = 0 → решений нет.")
    else:
        sol = -B / A
        steps.append(f"Коэффициент при x: A = {A}")
        steps.append(f"Свободный член: B = {B}")
        steps.append(f"Решение: x = -B / A = {sp.simplify(sol)}")
        roots.append(sol)

    return steps, roots


def solve_quadratic(eq, x, params):
    """Решает квадратное уравнение."""
    expr = eq.lhs - eq.rhs
    expr = expand(expr)
    a = expr.coeff(x, 2)
    b = expr.coeff(x, 1)
    c = expr.subs(x, 0)
    steps = []
    roots = []

    logger.debug(f"Квадратное: a={a}, b={b}, c={c}")

    # Проверяем, является ли a нулем (уравнение линейное)
    if sp.simplify(a) == 0:
        steps.append("Коэффициент a = 0 → уравнение вырождается в линейное.")
        lin_eq = Eq(b * x + c, 0)
        lin_steps, lin_roots = solve_linear(lin_eq, x, params)
        steps += lin_steps
        roots = lin_roots
    else:
        D = b ** 2 - 4 * a * c
        steps.append(f"Коэффициенты: a = {a}, b = {b}, c = {c}")
        steps.append(f"Дискриминант: D = b² - 4ac = {sp.simplify(D)}")

        # Проверяем, является ли D нулем
        if sp.simplify(D) == 0:
            x0 = -b / (2 * a)
            steps.append(f"D = 0 → один корень: x = {sp.simplify(x0)}")
            roots.append(x0)
        # Проверяем, является ли D отрицательным числом
        elif D.is_real and D.evalf() < 0:
            steps.append("D < 0 → действительных корней нет.")
        else:
            x1 = (-b + sqrt(D)) / (2 * a)
            x2 = (-b - sqrt(D)) / (2 * a)
            steps.append(f"Корни: x₁ = {sp.simplify(x1)}, x₂ = {sp.simplify(x2)}")
            roots.append(x1)
            roots.append(x2)

    return steps, roots


def solve_equation(eq_str):
    """Основная функция решения уравнения."""
    from parser import parse_equation

    try:
        eq, x, params = parse_equation(eq_str)
    except Exception as e:
        raise ValueError(f"Ошибка парсинга: {e}")

    # Теперь eq гарантированно является Eq(lhs, rhs)
    expr = eq.lhs - eq.rhs

    try:
        degree = sp.degree(expr, x)
    except Exception:
        degree = -1  # Если степень не может быть определена

    logger.debug(f"Степень уравнения по x: {degree}")

    steps = []
    roots = []

    if degree == 1:
        steps, roots = solve_linear(eq, x, params)
    elif degree == 2:
        steps, roots = solve_quadratic(eq, x, params)
    elif degree == 0:
        # Постоянный член
        constant_term = expr
        if sp.simplify(constant_term) == 0:
            steps.append("Уравнение превращается в 0 = 0 → решений бесконечно много.")
        else:
            steps.append(f"Уравнение превращается в {constant_term} = 0 → решений нет.")
    else:
        steps.append("Поддерживаются только линейные и квадратные уравнения.")

    return steps, x, params, expr, roots  # Возвращаем корни как отдельный параметр