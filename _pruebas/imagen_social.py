# -*- coding: utf-8 -*-
"""Compone la imagen que se ve al compartir un enlace del blog.

Es la que sale en Instagram, en WhatsApp, en X y en Bluesky cuando alguien
pega una dirección de Cinco Hache. Sin ella el enlace aparece como un
rectángulo de texto gris, que es lo que más desanima a pinchar.

Mide 1200 × 630 porque es lo que piden todas las redes, y usa las
tipografías del propio blog —Grenze y Spectral— convertidas desde los
woff2 que ya están en assets/fonts.

    python _pruebas/imagen_social.py

Se ejecuta a mano y muy de vez en cuando: cuando cambie la marca o el lema.
El resultado se versiona como cualquier otra imagen.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
MARCA = RAIZ / "assets" / "img" / "marca"
DESTINO = RAIZ / "assets" / "img" / "social.png"

ANCHO, ALTO = 1200, 630

FAMILIAS = ("ch-titular-500", "ch-texto", "ch-mono")

# La paleta del tema oscuro, tal cual está en _sass/_variables.scss.
FONDO = (15, 14, 13)
TINTA = (242, 239, 230)
TINTA_2 = (200, 194, 182)
TENUE = (125, 118, 107)
ACENTO = (137, 26, 26)


def preparar_fuentes(carpeta: Path) -> Path:
    """Saca los .ttf de los .woff2 que ya están en el blog.

    Pillow no sabe leer woff2, y las dos tipografías del blog solo están en
    ese formato. Se convierten aquí, a una carpeta de paso, para no tener que
    guardar los mismos tipos dos veces en el repositorio.
    """
    if all((carpeta / f"{n}.ttf").exists() for n in FAMILIAS):
        return carpeta
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        print("Falta fontTools para leer las tipografías del blog:")
        print("  py -m pip install fonttools brotli")
        raise SystemExit(1)

    carpeta.mkdir(parents=True, exist_ok=True)
    for n in FAMILIAS:
        origen = RAIZ / "assets" / "fonts" / f"{n}.woff2"
        if not origen.exists():
            print(f"No encuentro {origen.relative_to(RAIZ)}")
            raise SystemExit(1)
        f = TTFont(origen)
        f.flavor = None
        f.save(carpeta / f"{n}.ttf")
    print(f"  tipografías preparadas en {carpeta}")
    return carpeta


def fuente(ruta: Path, tamano: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(ruta), tamano)


def main(carpeta_fuentes: Path) -> int:
    carpeta_fuentes = preparar_fuentes(carpeta_fuentes)
    lienzo = Image.new("RGB", (ANCHO, ALTO), FONDO)
    pincel = ImageDraw.Draw(lienzo)

    titular = fuente(carpeta_fuentes / "ch-titular-500.ttf", 104)
    texto = fuente(carpeta_fuentes / "ch-texto.ttf", 31)
    mono = fuente(carpeta_fuentes / "ch-mono.ttf", 19)

    # Nada de lemas inventados aquí. El nombre, lo que escribe y quién lo
    # firma; el resto lo pone la red social sola.
    lema = ["Actualidad, hostelería", "y lo que me interese."]
    firma = "JAIME VÁZQUEZ DE PRADA SÁEZ"

    def caja_de(cadena, f):
        return pincel.textbbox((0, 0), cadena, font=f)

    # ── Medir todo antes de colocar nada ─────────────────────────────────
    # Las alturas de textbbox no incluyen el hueco de ascendentes y
    # descendentes, así que para repartir el espacio se usa el alto de línea
    # de cada fuente, que sí es el que ocupa de verdad.

    def alto_linea(f):
        a, d = f.getmetrics()
        return a + d

    HUECO_LEMA = 30
    HUECO_FIRMA = 30
    h_nombre = alto_linea(titular)
    h_lema = alto_linea(texto) + 8
    h_firma = alto_linea(mono)

    bloque = h_nombre + HUECO_LEMA + h_lema * len(lema) + HUECO_FIRMA + h_firma

    ancho_texto = max(
        [caja_de("Cinco Hache", titular)[2]]
        + [caja_de(l, texto)[2] for l in lema]
        + [caja_de(firma, mono)[2]]
    )

    # ── Centrar el conjunto: marca + hueco + texto ───────────────────────
    logo = Image.open(MARCA / "5h-marca-transparente-1024.png").convert("RGBA")
    lado = 330
    logo = logo.resize((lado, lado), Image.LANCZOS)

    HUECO_MARCA = 48
    conjunto = lado + HUECO_MARCA + ancho_texto
    izquierda = (ANCHO - conjunto) // 2

    lienzo.paste(logo, (izquierda, (ALTO - lado) // 2), logo)

    x = izquierda + lado + HUECO_MARCA
    y = (ALTO - bloque) // 2

    # ── El nombre ────────────────────────────────────────────────────────
    pincel.text((x, y), "Cinco Hache", font=titular, fill=TINTA)
    y += h_nombre + HUECO_LEMA

    # ── Lo que escribe ───────────────────────────────────────────────────
    for linea in lema:
        pincel.text((x, y), linea, font=texto, fill=TINTA_2)
        y += h_lema

    # ── Quién lo firma ───────────────────────────────────────────────────
    y += HUECO_FIRMA
    pincel.text((x, y), firma, font=mono, fill=TENUE)

    # ── Un filete de acento abajo, como el del blog ──────────────────────
    pincel.rectangle([0, ALTO - 9, ANCHO, ALTO], fill=ACENTO)

    lienzo.save(DESTINO, "PNG", optimize=True)
    print(f"  {DESTINO.relative_to(RAIZ)} · {ANCHO}×{ALTO} · "
          f"{DESTINO.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    import tempfile
    carpeta = (Path(sys.argv[1]) if len(sys.argv) > 1
               else Path(tempfile.gettempdir()) / "cincohache-fuentes")
    raise SystemExit(main(carpeta))
