#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_centres.py — où poser un visage à l'intérieur de chaque pays.

Pour chaque pays de data/pays.json : son morceau principal (la France sans la
Guyane, les États-Unis sans l'Alaska), le cadre qui l'entoure, et le plus grand
cercle qui tient dedans. Écrit data/centres.json. À relancer seulement si
data/pays.json change.

Tout est calculé dans la projection de la carte (Mercator), en unités où le
monde va de 0 à 1 : c'est là que le visage sera dessiné.
"""
import io, json, math, os
RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

def mercator(p):
    lat = max(-85.0, min(85.0, p[1]))
    return ((p[0] + 180) / 360.0,
            0.5 - math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) / (2 * math.pi))

def aire_vraie(anneau):
    """Proportionnelle à la surface réelle, sans l'exagération du nord."""
    s = 0.0
    for (x1, y1), (x2, y2) in zip(anneau, anneau[1:]):
        s += (x2 - x1) * (math.sin(math.radians(y1)) + math.sin(math.radians(y2)))
    return abs(s)

def distance(px, py, anneaux):
    """Distance au bord, positive à l'intérieur."""
    dedans, mini = False, 9.0
    for a in anneaux:
        for (x1, y1), (x2, y2) in zip(a, a[1:]):
            if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
                dedans = not dedans
            dx, dy = x2 - x1, y2 - y1
            n = dx * dx + dy * dy
            t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / n)) if n else 0.0
            d = (px - x1 - t * dx) ** 2 + (py - y1 - t * dy) ** 2
            if d < mini:
                mini = d
    return math.sqrt(mini) * (1 if dedans else -1)

def cercle(anneaux, boite):
    x0, y0, x1, y1 = boite
    mieux = (-9.0, 0, 0)
    cote = max(x1 - x0, y1 - y0) / 24.0
    nx, ny = max(1, int((x1 - x0) / cote)), max(1, int((y1 - y0) / cote))
    for i in range(nx + 1):
        for j in range(ny + 1):
            x, y = x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny
            mieux = max(mieux, (distance(x, y, anneaux), x, y))
    pas = cote
    for _ in range(9):
        pas /= 2
        r, x, y = mieux
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                mieux = max(mieux, (distance(x + dx * pas, y + dy * pas, anneaux),
                                    x + dx * pas, y + dy * pas))
    return mieux

with io.open(os.path.join(RACINE, "data", "pays.json"), encoding="utf-8") as f:
    pays = json.load(f)["features"]
sortie = {}
for e in pays:
    iso, g = e["properties"]["iso"], e["geometry"]
    polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    ordre = sorted(range(len(polys)), key=lambda i: -aire_vraie(polys[i][0]))
    morceaux = [(iso, ordre[0])]
    # Le Danemark a deux visages : le sien, et celui du Groenland, son plus
    # grand morceau (clef « DNK+ »).
    if iso == "DNK":
        morceaux = [(iso, next(i for i in ordre if polys[i][0][0][0] > 0)), ("DNK+", ordre[0])]
    for cle, n in morceaux:
        anneaux = [[mercator(p) for p in a] for a in polys[n]]
        xs, ys = [p[0] for p in anneaux[0]], [p[1] for p in anneaux[0]]
        boite = (min(xs), min(ys), max(xs), max(ys))
        r, x, y = cercle(anneaux, boite)
        sortie[cle] = {"m": n, "b": [round(v, 6) for v in boite],
                       "c": [round(x, 6), round(y, 6)], "r": round(max(r, 1e-6), 7)}
with io.open(os.path.join(RACINE, "data", "centres.json"), "w", encoding="utf-8") as f:
    json.dump(sortie, f, separators=(",", ":"))
print(len(sortie), "pays")
