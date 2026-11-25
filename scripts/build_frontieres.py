#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_frontieres.py — les frontières FINES, pour les cartes où l'on zoome
jusqu'à la rue (métros, entreprises cotées).

Pourquoi : data/frontieres.json vient de Natural Earth, juste à un ou deux
kilomètres près. De loin, rien ne se voit. De près, le terminus du métro de
Lille (CH Dron, à Tourcoing) tombait en Belgique (remarqué par Antonin le
25 novembre 2026) : c'était la frontière qui était fausse, pas le métro.

Ce que fait ce script : il prend les frontières d'OpenStreetMap, justes à
quelques mètres, mais seulement celles que le site reconnaît. La règle :

  - un trait d'OpenStreetMap n'est gardé que s'il passe tout près d'un trait
    de data/frontieres.json. La ligne de Perekop (Crimée), celle du Sahara
    occidental, de Chypre du Nord ou du Somaliland n'ont aucun voisin dans ce
    fichier : elles tombent d'elles-mêmes ;
  - un trait du site qui n'a aucun voisin dans OpenStreetMap est gardé tel
    quel.

Le résultat est coupé en carrés de 5 degrés, data/frontieres/x_y.json : le
navigateur ne télécharge que ceux qu'il regarde.

À lancer :  python3 scripts/build_frontieres.py     (--neuf : tout retélécharger)
Les frontières bougent très peu : une fois par an suffit largement.
"""

import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.join(ICI, "..")
CACHE = os.path.join(ICI, ".cache-metro")
SORTIE = os.path.join(RACINE, "data", "frontieres")
OVERPASS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
EN_TETES = {"User-Agent": "StatsMaps/1.0 (+https://statsmaps.com)"}

PAVE = 10          # degrés : la taille des morceaux demandés à OpenStreetMap
CARREAU = 5        # degrés : la taille des fichiers écrits
VOISIN_KM = 6.0    # « tout près » : l'erreur de Natural Earth, avec de la marge
TOLERANCE_M = 15.0 # précision gardée


def dit(*a):
    print(*a, flush=True)


# --- 1. OpenStreetMap -----------------------------------------------------

def demander(s, o, n, e):
    q = ('[out:json][timeout:300];'
         'way["boundary"="administrative"]["admin_level"="2"]["maritime"!="yes"]'
         '["natural"!="coastline"](%s,%s,%s,%s);out skel geom;' % (s, o, n, e))
    for essai in range(16):
        try:
            r = urllib.request.Request(OVERPASS[essai % 2], data=("data=" + urllib.parse.quote(q)).encode(),
                                       headers=EN_TETES)
            with urllib.request.urlopen(r, timeout=320) as f:
                d = json.loads(f.read().decode("utf-8"))
            if "remark" in d and "error" in d["remark"]:
                raise RuntimeError(d["remark"][:120])
            return d
        except Exception as ex:
            dit("    …", type(ex).__name__, str(ex)[:100])
            time.sleep(min(90, 10 * (essai + 1)))
    raise RuntimeError("Overpass ne répond pas : relancer plus tard, "
                       "ce qui est déjà téléchargé est gardé")


def moissonner(traits):
    """Les voies d'OpenStreetMap, pavé par pavé. On ne demande que les pavés
    où le site a une frontière."""
    paves = sorted({(int(math.floor(p[1] / PAVE)) * PAVE, int(math.floor(p[0] / PAVE)) * PAVE)
                    for t in traits for p in t})
    voies = {}
    for i, (s, o) in enumerate(paves):
        chemin = os.path.join(CACHE, "frontieres_%d_%d.json" % (s, o))
        if not os.path.exists(chemin) or "--neuf" in sys.argv:
            d = demander(s, o, s + PAVE, o + PAVE)
            utile = {str(w["id"]): [[p["lon"], p["lat"]] for p in w.get("geometry", []) if p]
                     for w in d.get("elements", [])}
            with open(chemin, "w") as f:
                json.dump(utile, f)
            time.sleep(4)
        with open(chemin) as f:
            lu = json.load(f)
        voies.update(lu)
        dit("  pavé %d/%d (%d, %d) : %d voies" % (i + 1, len(paves), s, o, len(lu)))
    return list(voies.values())


# --- 2. Qui est voisin de qui ? -------------------------------------------

def km(a, b):
    k = math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot((a[0] - b[0]) * k, a[1] - b[1]) * 111.2


class Voisinage:
    """Répond vite à « y a-t-il un trait à moins de VOISIN_KM d'ici ? ». Les
    traits y sont semés de points tous les kilomètres, rangés par case."""

    def __init__(self, traits):
        self.cases = {}
        for t in traits:
            for a, b in zip(t, t[1:]):
                n = max(1, int(km(a, b)))
                for i in range(n + 1):
                    p = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
                    self.cases.setdefault(self.case(p), []).append(p)

    @staticmethod
    def case(p):
        return (int(math.floor(p[0] * 5)), int(math.floor(p[1] * 10)))

    def pres(self, p, limite=VOISIN_KM):
        cx, cy = self.case(p)
        # Une case fait 0,2° × 0,1° ; plus on monte vers le pôle, plus il faut
        # regarder de cases en largeur.
        l = 1 + int(limite / (22.2 * max(0.1, math.cos(math.radians(p[1])))))
        for x in range(cx - l, cx + l + 1):
            for y in range(cy - 1, cy + 2):
                for q in self.cases.get((x, y), ()):
                    if km(p, q) < limite:
                        return True
        return False


def garder_les_voisins(traits, voisinage, garder=True):
    """Les morceaux de traits proches (ou au contraire éloignés) du voisinage."""
    sortie = []
    for t in traits:
        # On coupe les longs segments : l'un de leurs bouts peut être proche et
        # l'autre non.
        fin = [t[0]]
        for a, b in zip(t, t[1:]):
            n = max(1, int(km(a, b) / 2))
            fin += [[a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n]
                    for i in range(1, n + 1)]
        morceau = []
        for p in fin:
            if voisinage.pres(p) == garder:
                morceau.append(p)
            else:
                if len(morceau) > 1:
                    sortie.append(morceau)
                morceau = []
        if len(morceau) > 1:
            sortie.append(morceau)
    return sortie


# --- 3. Alléger et écrire -------------------------------------------------

def alleger(points, tolerance_m=TOLERANCE_M):
    """Douglas-Peucker, sans récursion."""
    if len(points) < 3:
        return points
    kx = 111320.0 * math.cos(math.radians(points[len(points) // 2][1]))
    ky = 110540.0
    garder = {0, len(points) - 1}
    pile = [(0, len(points) - 1)]
    while pile:
        d, f = pile.pop()
        ax, ay = points[d][0] * kx, points[d][1] * ky
        dx, dy = points[f][0] * kx - ax, points[f][1] * ky - ay
        norme = dx * dx + dy * dy
        pire, ou = 0.0, -1
        for i in range(d + 1, f):
            px, py = points[i][0] * kx - ax, points[i][1] * ky - ay
            t = max(0.0, min(1.0, (px * dx + py * dy) / norme)) if norme else 0.0
            e = math.hypot(px - t * dx, py - t * dy)
            if e > pire:
                pire, ou = e, i
        if pire > tolerance_m:
            garder.add(ou)
            pile += [(d, ou), (ou, f)]
    return [points[i] for i in sorted(garder)]


def ecrire(traits):
    carreaux = {}
    for t in traits:
        t = [[round(x, 5), round(y, 5)] for x, y in alleger(t)]
        # Un trait est rangé dans tous les carreaux qu'il touche, coupé à leurs
        # bords (un point de plus de chaque côté, pour que tout se raccorde).
        courant, morceau = None, []
        for a, b in zip(t, t[1:]):
            c = (int(math.floor((a[0] + b[0]) / 2 / CARREAU)),
                 int(math.floor((a[1] + b[1]) / 2 / CARREAU)))
            if c != courant:
                if len(morceau) > 1:
                    carreaux.setdefault(courant, []).append(morceau)
                courant, morceau = c, [a]
            morceau.append(b)
        if len(morceau) > 1:
            carreaux.setdefault(courant, []).append(morceau)

    os.makedirs(SORTIE, exist_ok=True)
    for nom in os.listdir(SORTIE):
        if nom.endswith(".json"):
            os.remove(os.path.join(SORTIE, nom))
    total = 0
    for (x, y), morceaux in carreaux.items():
        texte = json.dumps(morceaux, separators=(",", ":"))
        total += len(texte)
        with open(os.path.join(SORTIE, "%d_%d.json" % (x, y)), "w") as f:
            f.write(texte)
    # La liste des carreaux qui existent : le navigateur n'en demande pas d'autres.
    with open(os.path.join(SORTIE, "liste.json"), "w") as f:
        json.dump(sorted("%d_%d" % c for c in carreaux), f)
    dit("  %d carreaux, %d Ko" % (len(carreaux), total // 1024))


if __name__ == "__main__":
    with open(os.path.join(RACINE, "data", "frontieres.json"), encoding="utf-8") as f:
        site = [t for e in json.load(f)["features"] for t in
                ([e["geometry"]["coordinates"]] if e["geometry"]["type"] == "LineString"
                 else e["geometry"]["coordinates"])]
    os.makedirs(CACHE, exist_ok=True)
    dit("→ OpenStreetMap : les frontières")
    osm = [t for t in moissonner(site) if len(t) > 1]
    dit("→ Tri : celles que le site reconnaît")
    gardes = garder_les_voisins(osm, Voisinage(site))
    restes = garder_les_voisins(site, Voisinage(gardes), garder=False)
    dit("  %d traits d'OpenStreetMap gardés sur %d ; %d morceaux du site sans équivalent"
        % (len(gardes), len(osm), len(restes)))
    dit("→ Écriture de data/frontieres/")
    ecrire(gardes + restes)
    dit("✓ Terminé.")
