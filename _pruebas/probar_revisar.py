# -*- coding: utf-8 -*-
"""Comprueba que las comprobaciones comprueban algo.

Una salvaguarda que nunca salta da una confianza que no se ha ganado, y es
peor que no tener ninguna. Así que aquí se rompe el sitio a propósito, una
avería cada vez, y se exige que `revisar.py` la pille.

Cada avería de esta lista es la reproducción de un fallo que ocurrió de
verdad. Si algún día alguna deja de detectarse, esto se pone en rojo.

    python _pruebas/probar_revisar.py
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REVISAR = RAIZ / "_pruebas" / "revisar.py"


# ── Las averías ──────────────────────────────────────────────────────────
# Cada una recibe la copia del sitio y la estropea de una manera concreta.

def scss_en_crudo(sitio: Path) -> None:
    """Lo que publicaba GitHub Pages en modo «rama»: 182 bytes de @use."""
    css = next((sitio / "assets" / "css").glob("*.css"))
    css.write_text('@use "variables";@use "fuentes";@use "reset";\n', encoding="utf-8")


def css_sin_tipografias(sitio: Path) -> None:
    css = next((sitio / "assets" / "css").glob("*.css"))
    t = css.read_text(encoding="utf-8")
    css.write_text(t.replace("@font-face", "x-font-face"), encoding="utf-8")


def recurso_que_no_esta(sitio: Path) -> None:
    """Una tipografía que solo pide el CSS, no precargada desde el HTML.

    Si se borra una de las precargadas salta antes la comprobación de
    recursos, que también acierta; aquí interesa la del CSS.
    """
    html = "".join(p.read_text(encoding="utf-8", errors="replace")
                   for p in sitio.rglob("*.html"))
    for f in sorted((sitio / "assets" / "fonts").glob("*.woff2")):
        if f.name not in html:
            f.unlink()
            return
    raise RuntimeError("todas las tipografías están precargadas desde el HTML")


def imagen_vacia(sitio: Path) -> None:
    """El <img src=""> de la ficha de autor: la cadena vacía es verdadera."""
    p = sitio / "index.html"
    p.write_text(p.read_text(encoding="utf-8").replace("<body", '<img src=""><body', 1),
                 encoding="utf-8")


def liquid_escapado(sitio: Path) -> None:
    p = sitio / "index.html"
    p.write_text(p.read_text(encoding="utf-8") + "\n{{ page.titulo }}\n", encoding="utf-8")


def robots_envuelto(sitio: Path) -> None:
    """robots.txt sin `layout: null` sale dentro de la plantilla del sitio."""
    (sitio / "robots.txt").write_text(
        "<!doctype html><html><body>User-agent: *</body></html>", encoding="utf-8")


def sitemap_roto(sitio: Path) -> None:
    (sitio / "sitemap.xml").write_text("<urlset><url></urlset>", encoding="utf-8")


def manifiesto_roto(sitio: Path) -> None:
    (sitio / "manifiesto.webmanifest").write_text('{"name": "Cinco Hache",}', encoding="utf-8")


def falta_una_seccion(sitio: Path) -> None:
    shutil.rmtree(sitio / "ensayo")


def falta_el_sobre_mi(sitio: Path) -> None:
    shutil.rmtree(sitio / "acerca")


def pagina_sin_titulo(sitio: Path) -> None:
    p = sitio / "index.html"
    p.write_text(re.sub(r"<title>.*?</title>", "<title></title>", p.read_text(encoding="utf-8"),
                        flags=re.S), encoding="utf-8")


def descripcion_vacia(sitio: Path) -> None:
    """La misma trampa que el título: content="" parecía tener contenido."""
    p = sitio / "index.html"
    p.write_text(re.sub(r'(name="description"[^>]+content=")[^"]*"', r'"',
                        p.read_text(encoding="utf-8")), encoding="utf-8")


def rastro_de_ia(sitio: Path) -> None:
    """El encargo es que no quede ni uno, en ninguna parte."""
    p = sitio / "index.html"
    p.write_text(p.read_text(encoding="utf-8") + "\n<!-- Co-Authored-By: Claude -->\n",
                 encoding="utf-8")


def texto_de_relleno(sitio: Path) -> None:
    p = sitio / "index.html"
    p.write_text(p.read_text(encoding="utf-8").replace("</body>", "<p>Lorem ipsum</p></body>"),
                 encoding="utf-8")


AVERIAS = [
    ("SCSS sin compilar",            scss_en_crudo,        "compilado"),
    ("CSS sin tipografías",          css_sin_tipografias,  "paleta"),
    ("una tipografía que falta",     recurso_que_no_esta,  "tipografías del CSS"),
    ("un <img src=\"\"> vacío",      imagen_vacia,         "atributos vacíos"),
    ("Liquid escapado al HTML",      liquid_escapado,      "Liquid al HTML"),
    ("robots.txt envuelto en HTML",  robots_envuelto,      "robots.txt"),
    ("sitemap mal formado",          sitemap_roto,         "sitemap"),
    ("manifiesto con JSON roto",     manifiesto_roto,      "manifiesto"),
    ("una sección sin página",       falta_una_seccion,    "secciones.yml"),
    ("el Sobre mí desaparecido",     falta_el_sobre_mi,    "páginas de siempre"),
    ("una página sin título",        pagina_sin_titulo,    "título y descripción"),
    ("una descripción vacía",        descripcion_vacia,    "título y descripción"),
    ("un rastro de IA",              rastro_de_ia,         "rastro de IA"),
    ("texto de relleno",             texto_de_relleno,     "texto de relleno"),
]


def revisar(sitio: Path) -> tuple[int, str]:
    entorno = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run(
        [sys.executable, str(REVISAR), str(sitio)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=entorno,
    )
    return r.returncode, (r.stdout or "") + (r.stderr or "")


# Lo contrario de una avería: algo que PARECE un problema y no lo es. Si
# esto empieza a fallar, la comprobación se ha vuelto demasiado nerviosa y
# hay que apretarla, no relajar el sitio.
FALSAS_ALARMAS = [
    (
        "un placeholder= de toda la vida",
        lambda sitio: (sitio / "index.html").write_text(
            (sitio / "index.html").read_text(encoding="utf-8").replace(
                "</body>", '<input placeholder="tu@correo.com"></body>'),
            encoding="utf-8"),
    ),
    (
        "una clase que se llama «todo:»",
        lambda sitio: (sitio / "index.html").write_text(
            (sitio / "index.html").read_text(encoding="utf-8").replace(
                "</body>", '<script>var x = "TODO: nada";</script></body>'),
            encoding="utf-8"),
    ),
]


def main() -> int:
    original = RAIZ / "_site"
    if not original.is_dir():
        print("No hay _site. Compila el sitio antes:  bundle exec jekyll build")
        return 1

    print("\nEl sitio intacto debería pasar")
    codigo, salida = revisar(original)
    if codigo != 0:
        print("  FALLA: el sitio bueno no pasa la revisión.")
        print("\n".join("    " + l for l in salida.splitlines()[-14:]))
        return 1
    print("  ok\n")

    print(f"Rompiéndolo de {len(AVERIAS)} maneras, a ver si se entera\n")
    malas = []
    for nombre, romper, esperado in AVERIAS:
        with tempfile.TemporaryDirectory(prefix="ch-revisar-") as tmp:
            copia = Path(tmp) / "sitio"
            shutil.copytree(original, copia)
            romper(copia)
            codigo, salida = revisar(copia)

            if codigo == 0:
                print(f"  SE ESCAPA  {nombre}")
                malas.append(f"{nombre}: no se detecta")
            elif esperado.lower() not in salida.lower():
                print(f"  CONFUNDE   {nombre} (salta otra comprobación, no «{esperado}»)")
                malas.append(f"{nombre}: lo detecta la comprobación equivocada")
            else:
                print(f"  la pilla   {nombre}")

    print(f"\nY {len(FALSAS_ALARMAS)} cosas que parecen averías y no lo son\n")
    for nombre, tocar in FALSAS_ALARMAS:
        with tempfile.TemporaryDirectory(prefix="ch-revisar-") as tmp:
            copia = Path(tmp) / "sitio"
            shutil.copytree(original, copia)
            tocar(copia)
            codigo, salida = revisar(copia)
            if codigo != 0:
                print(f"  SE ASUSTA  {nombre}")
                malas.append(f"{nombre}: falso positivo")
            else:
                print(f"  no pica    {nombre}")

    print()
    if malas:
        print(f"  {len(malas)} avería(s) sin cubrir:")
        for m in malas:
            print(f"    · {m}")
        return 1
    print(f"  Las {len(AVERIAS)} averías se detectan. Las salvaguardas valen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
