# code-golf-expr — NovaKernel entry

`main.js` exports `evalExpr(s)`: a recursive-descent evaluator for the tiny
arithmetic language (`+ - * /`, decimals, parentheses, precedence, unary
minus, optional spaces). No dependencies.

Metric is source bytes: **444 bytes**.

Verified locally against all 9 public cases plus extras
(`-3+2`, `2*-3`, spaced input, `.5*4`, nested parens, left-associative
division) — all correct.
