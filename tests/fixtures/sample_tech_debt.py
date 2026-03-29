"""Sample Python file with technical debt issues (used in tests)."""


# TD001: TODO comment
# TODO: refactor this whole module


# TD002: Long function (> 50 lines)
def very_long_function(a, b, c, d, e, f):  # TD005: too many params
    x = a + b
    y = c + d
    z = e + f
    w = x + y
    r = w + z
    s = r * 2
    t = s - 1
    u = t + 3
    v = u * 4
    aa = v - 2
    bb = aa + 1
    cc = bb * 3
    dd = cc - 5
    ee = dd + 7
    ff = ee * 2
    gg = ff - 3
    hh = gg + 8
    ii = hh * 9
    jj = ii - 1
    kk = jj + 2
    ll = kk * 5
    mm = ll - 6
    nn = mm + 4
    oo = nn * 7
    pp = oo - 8
    qq = pp + 9
    rr = qq * 1
    ss = rr - 2
    tt = ss + 3
    uu = tt * 4
    vv = uu - 5
    ww = vv + 6
    xx = ww * 7
    yy = xx - 8
    zz = yy + 9
    result1 = zz * 10
    result2 = result1 - 11
    result3 = result2 + 12
    result4 = result3 * 13
    result5 = result4 - 14
    result6 = result5 + 15
    result7 = result6 - 16
    result8 = result7 + 17
    result9 = result8 * 18
    result10 = result9 - 19
    result11 = result10 + 20
    result12 = result11 * 21
    result13 = result12 - 22
    result14 = result13 + 23
    result15 = result14 * 24
    return result15


# TD004: Magic number
def calculate_price(quantity):
    discount = quantity * 0.15  # magic number
    total = quantity * 99.99    # magic number
    return total - discount


# TD006: Deep nesting
def deeply_nested(data):
    if data:
        for item in data:
            if item:
                for sub in item:
                    if sub:  # depth 4 → triggers TD006
                        pass
