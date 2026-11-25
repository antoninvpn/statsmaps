#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_drapeaux.py — fabrique assets/drapeaux/*.png à partir des *.svg.

Pourquoi des PNG : un SVG est fait de couches superposées, et à certains zooms
Safari laisse voir celles du dessous au bord du drapeau (un liseré clair,
remarqué par Antonin en novembre 2026). Une image n'a qu'une couche.

À lancer sur le Mac après avoir touché à un SVG (il faut Google Chrome, qui
dessine les images), puis augmenter VERSION_DRAPEAUX dans assets/js/drapeaux.js :
    python3 scripts/build_drapeaux.py
"""
import base64, glob, json, os, re, subprocess, sys, tempfile
RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DOSSIER = os.path.join(RACINE, "assets", "drapeaux")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
LARGEUR, HAUTEUR = 160, 120   # huit fois la taille affichée : net partout

svg = {os.path.basename(f)[:-4]: base64.b64encode(open(f, "rb").read()).decode()
       for f in sorted(glob.glob(os.path.join(DOSSIER, "*.svg")))}
page = """<!doctype html><meta charset=utf-8><pre id=sortie></pre><script>
const S=%s,L=%d,H=%d;(async()=>{const o={};for(const n in S){const i=new Image();
i.src='data:image/svg+xml;base64,'+S[n];await i.decode();
const c=document.createElement('canvas');c.width=L;c.height=H;
const x=c.getContext('2d');
/* Dessiné huit fois au même endroit : entre deux bandes, le SVG laisse parfois
   un jour presque invisible, qui se bouche ainsi. Le Népal, seul drapeau qui
   n'est pas rectangulaire, reste transparent autour et n'est dessiné qu'une fois. */
for(let k=0;k<(n==='np'?1:8);k++)x.drawImage(i,0,0,L,H);
o[n]=c.toDataURL('image/png').slice(22);}
document.getElementById('sortie').textContent='DEBUT'+JSON.stringify(o)+'FIN';})();
</script>""" % (json.dumps(svg), LARGEUR, HAUTEUR)
with tempfile.TemporaryDirectory() as t:
    chemin = os.path.join(t, "p.html")
    with open(chemin, "w") as f:
        f.write(page)
    dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--user-data-dir=" + t + "/profil",
                          "--virtual-time-budget=60000", "--dump-dom", "file://" + chemin],
                         capture_output=True, text=True, timeout=180).stdout
m = re.search(r"DEBUT(\{.*?\})FIN</pre>", dom, re.S)
if not m:
    sys.exit("✗ Chrome n'a rien rendu : rien n'est écrit.")
png = json.loads(m.group(1))
if set(png) != set(svg):
    sys.exit("✗ Il manque des drapeaux : rien n'est écrit.")
for n, b in png.items():
    with open(os.path.join(DOSSIER, n + ".png"), "wb") as f:
        f.write(base64.b64decode(b))
print(len(png), "drapeaux écrits")
