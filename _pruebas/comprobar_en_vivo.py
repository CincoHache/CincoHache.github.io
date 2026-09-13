# -*- coding: utf-8 -*-
"""Comprueba el sitio ya publicado, no el que acaba de compilarse.

Revisar `_site` no basta. El desastre de los estilos ocurrió con `_site`
perfecto: GitHub lo tiraba a la basura y publicaba otra cosa. Entre lo que
compilamos y lo que ve un lector hay un tramo —el despliegue— donde las cosas
también se rompen, y hasta ahora nadie miraba ese tramo.

    python _pruebas/comprobar_en_vivo.py https://cincohache.github.io <sha>

El `sha` es opcional. Si se pasa, se exige que la página publicada lleve ese
commit: es la única manera de distinguir «se ha desplegado bien» de «sigue
viéndose lo de antes», que es lo que pasó dos veces el primer día.
"""

from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

for flujo in (sys.stdout, sys.stderr):
    try:
        flujo.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

RAIZ = Path(__file__).resolve().parent.parent
ESPERA = 30

fallos: list[str] = []


def traer(url: str) -> tuple[int, bytes]:
    peticion = urllib.request.Request(url, headers={
        "User-Agent": "cincohache-comprobacion",
        # Sin esto, la caché del CDN puede devolver lo de antes y dar por
        # bueno un despliegue que no ha llegado.
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    try:
        with urllib.request.urlopen(peticion, timeout=ESPERA) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:                          # noqa: BLE001
        print(f"         ({e.__class__.__name__}: {e})")
        return 0, b""


def comprobar(titulo: str, problemas: list[str]) -> None:
    if problemas:
        fallos.append(titulo)
        print(f"  FALLA  {titulo}")
        for p in problemas[:8]:
            print(f"         {p}")
    else:
        print(f"  ok     {titulo}")


def main(base: str, sha: str = "") -> int:
    base = base.rstrip("/")
    print(f"\nComprobando {base} tal y como lo ve un lector\n")

    codigo, crudo = traer(base + "/")
    if codigo != 200:
        print(f"  FALLA  La portada devuelve {codigo}")
        return 1
    portada = crudo.decode("utf-8", errors="replace")
    print(f"  ok     La portada responde 200 ({len(crudo):,} bytes)")

    # ── ¿Estamos viendo lo último, o lo de antes? ────────────────────────
    if sha:
        m = re.search(r'name="ch-version"[^>]+content="([^"]+)"', portada)
        publicado = m.group(1) if m else ""
        comprobar(
            "Lo publicado es el último commit",
            [] if publicado.startswith(sha[:7]) else [
                f"esperaba {sha[:7]} y hay «{publicado[:12] or 'nada'}»: "
                f"el despliegue no ha llegado, o GitHub sirve una copia vieja"
            ],
        )

    # ── El fallo que dejó el sitio sin un solo estilo ────────────────────
    hojas = re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"', portada)
    problemas = []
    if not hojas:
        problemas.append("la portada no enlaza ninguna hoja de estilos")
    for h in hojas:
        codigo, cuerpo = traer(base + h if h.startswith("/") else h)
        texto = cuerpo.decode("utf-8", errors="replace")
        if codigo != 200:
            problemas.append(f"{h} devuelve {codigo}")
        elif "@use" in texto or "@import" in texto:
            problemas.append(f"{h} llega con @use sin compilar: Pages está en modo «rama»")
        elif len(cuerpo) < 10_000:
            problemas.append(f"{h} pesa {len(cuerpo)} bytes: es SCSS en crudo, no CSS")
    comprobar("El CSS que se sirve está compilado", problemas)

    # ── Que no falte nada de lo que la página pide ───────────────────────
    recursos = set(re.findall(r'(?:src|href)="(/[^"#?]+\.[a-z0-9]{2,5})"', portada, re.I))
    problemas = []
    for r in sorted(recursos):
        codigo, cuerpo = traer(base + r)
        if codigo != 200:
            problemas.append(f"{r} devuelve {codigo}")
        elif not cuerpo:
            problemas.append(f"{r} llega vacío")
    comprobar(f"Los {len(recursos)} recursos de la portada se sirven", problemas)

    # ── Las páginas que siempre tienen que estar ─────────────────────────
    rutas = ["/acerca/", "/trabajos/", "/robots.txt", "/sitemap.xml", "/404.html"]
    texto = (RAIZ / "_data" / "secciones.yml").read_text(encoding="utf-8")
    rutas += re.findall(r"^\s+url:\s*(\S+)", texto, re.M)

    problemas = []
    for r in rutas:
        codigo, cuerpo = traer(base + r)
        if codigo != 200:
            problemas.append(f"{r} devuelve {codigo}")
        elif r == "/robots.txt" and cuerpo.lstrip().startswith(b"<"):
            problemas.append("robots.txt se sirve como HTML")
    comprobar(f"Las {len(rutas)} páginas de siempre responden", problemas)

    print()
    if fallos:
        print(f"  {len(fallos)} comprobación(es) fallan sobre el sitio publicado:")
        for f in fallos:
            print(f"    · {f}")
        return 1
    print("  El sitio publicado está entero.")
    return 0


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else "https://cincohache.github.io"
    sha = sys.argv[2] if len(sys.argv) > 2 else ""
    raise SystemExit(main(base, sha))
