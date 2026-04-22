"""安全的简易 DSL 求值器。
支持: AND OR NOT > < >= <= = != IN BETWEEN ABS()
不使用 Python eval,避免任意代码执行。

⚠ 此实现专为演示设计,生产应换成成熟引擎(如 jsonlogic / opa)。
"""
import re
import operator
from typing import Any, Dict


_OPS = {
    ">": operator.gt, "<": operator.lt,
    ">=": operator.ge, "<=": operator.le,
    "=": operator.eq, "==": operator.eq, "!=": operator.ne,
}


def _get(ctx: Dict[str, Any], path: str) -> Any:
    """支持 a.b.c 路径取值。"""
    cur: Any = ctx
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            cur = getattr(cur, part, None)
        if cur is None:
            return None
    return cur


def _coerce(v: str) -> Any:
    v = v.strip()
    if v.startswith("'") and v.endswith("'"):
        return v[1:-1]
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1]
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        return v


def _eval_atom(expr: str, ctx: Dict[str, Any]) -> bool:
    expr = expr.strip()
    # IN
    m = re.match(r"^([\w\.]+)\s+IN\s+\(([^)]+)\)$", expr, re.IGNORECASE)
    if m:
        left = _get(ctx, m.group(1))
        items = [_coerce(x) for x in m.group(2).split(",")]
        return left in items
    # BETWEEN
    m = re.match(r"^([\w\.]+)\s+BETWEEN\s+(\S+)\s+AND\s+(\S+)$", expr, re.IGNORECASE)
    if m:
        left = _get(ctx, m.group(1))
        if left is None:
            return False
        return _coerce(m.group(2)) <= left <= _coerce(m.group(3))
    # ABS(a - b) > c
    m = re.match(r"^ABS\(([\w\.]+)\s*-\s*([\w\.]+)\)\s*(>=|<=|>|<|=|!=)\s*(\S+)$", expr, re.IGNORECASE)
    if m:
        a, b, op, c = m.group(1), m.group(2), m.group(3), m.group(4)
        va, vb = _get(ctx, a), _get(ctx, b)
        if va is None or vb is None:
            return False
        return _OPS[op](abs(va - vb), _coerce(c))
    # 函数式: duplicate_in_24h(...)
    m = re.match(r"^([a-z_][\w]*)\((.*)\)$", expr, re.IGNORECASE)
    if m:
        # 演示: 函数调用降级为查 ctx 中是否有同名 flag
        return bool(ctx.get(m.group(1)))
    # 普通 a OP b
    m = re.match(r"^([\w\.]+)\s*(>=|<=|!=|==|=|>|<)\s*(.+)$", expr)
    if m:
        left = _get(ctx, m.group(1))
        right = _coerce(m.group(3))
        if left is None:
            return False
        try:
            return _OPS[m.group(2)](left, right)
        except TypeError:
            return False
    # 单变量 = 真值
    return bool(_get(ctx, expr))


def evaluate(expression: str, ctx: Dict[str, Any]) -> bool:
    """Top-level: 处理 AND / OR / NOT(目前不支持嵌套括号,演示足够)。"""
    expr = expression.strip()
    # OR 优先级更低
    parts = re.split(r"\s+OR\s+", expr, flags=re.IGNORECASE)
    if len(parts) > 1:
        return any(evaluate(p, ctx) for p in parts)
    parts = re.split(r"\s+AND\s+", expr, flags=re.IGNORECASE)
    if len(parts) > 1:
        return all(evaluate(p, ctx) for p in parts)
    if expr.upper().startswith("NOT "):
        return not evaluate(expr[4:], ctx)
    return _eval_atom(expr, ctx)
