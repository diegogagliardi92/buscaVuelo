from buscavuelo import combinar

ida = {"2026-11-10": {"precio": 100}, "2026-11-12": {"precio": 50}}
vuelta = {"2026-11-13": {"precio": 10}, "2026-11-20": {"precio": 1}}
c = combinar(ida, vuelta, 1, 4)
assert [(x[0], x[1], x[3], x[5]) for x in c] == [(60, "2026-11-12", "2026-11-13", 1), (110, "2026-11-10", "2026-11-13", 3)], c
print("ok")

# finde: 2026-11-12 es jueves, 2026-11-13 viernes
ida = {"2026-11-12": {"precio": 5}, "2026-11-13": {"precio": 7}, "2026-11-14": {"precio": 1}}
vuelta = {"2026-11-15": {"precio": 1}, "2026-11-16": {"precio": 1}, "2026-11-17": {"precio": 1}}
c = combinar(ida, vuelta, 3, 3, {3, 4})
assert [(x[1], x[3]) for x in c] == [("2026-11-12", "2026-11-15"), ("2026-11-13", "2026-11-16")], c
print("ok finde")
