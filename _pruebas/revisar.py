# -*- coding: utf-8 -*-
"""Revisa el sitio ya compilado antes de dejar que se publique.

Todas las comprobaciones de aquí vienen de algo que se rompió de verdad. No
hay ninguna puesta por si acaso: si una existe es porque un día el sitio salió
mal por eso y nadie se enteró hasta verlo publicado.

Lo que más duele de estos fallos es que **ninguno da error**. Jekyll compila
tan contento, GitHub pone el tick verde, y la web queda rota. Por eso hace
falta mirar el resultado y no fiarse de que el proceso terminara bien.

    python _pruebas/revisar.py _site

Devuelve 0 si todo está en su sitio y 1 si algo falla, que es lo que hace que
el despliegue se pare.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from xml.etree import ElementTree

# La consola de Windows escribe en cp1252 y se come los acentos, que aquí
# van en todos los mensajes. En el registro de GitHub se ven igual de mal.
for flujo in (sys.stdout, sys.stderr):
    try:
        flujo.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

RAIZ = Path(__file__).resolve().parent.parent

fallos: list[str] = []
avisos: list[str] = []
hechas = 0


def comprobar(titulo: str):
    """Decorador que registra una comprobación y recoge lo que encuentre."""
    def envolver(fn):
        global hechas
        hechas += 1
        try:
            problemas = fn() or []
        except Exception as e:                      # noqa: BLE001
            problemas = [f"la comprobación reventó: {e.__class__.__name__}: {e}"]
        if problemas:
            fallos.append(titulo)
            print(f"  FALLA  {titulo}")
            for p in problemas[:8]:
                print(f"         {p}")
            if len(problemas) > 8:
                print(f"         … y {len(problemas) - 8} más")
        else:
            print(f"  ok     {titulo}")
        return fn
    return envolver


def avisar(titulo: str, problemas: list[str]) -> None:
    """Como `comprobar`, pero no detiene el despliegue."""
    if problemas:
        avisos.append(titulo)
        print(f"  AVISO  {titulo}")
        for p in problemas[:6]:
            print(f"         {p}")


def _texto_visible(html: str) -> str:
    """Lo que se lee en la página: sin etiquetas, sin guiones, sin código.

    Los scripts y los estilos se quitan enteros, con su contenido: dentro
    hay cadenas y nombres de clase que no los lee nadie y que dispararían
    comprobaciones pensadas para el texto.
    """
    html = re.sub(r"<(script|style)\b.*?</\1\s*>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


def main(destino: Path) -> int:
    if not destino.is_dir():
        print(f"No existe {destino}. ¿Has compilado el sitio?")
        return 1

    paginas = sorted(destino.rglob("*.html"))
    print(f"\nRevisando {destino} — {len(paginas)} páginas\n")

    # ── El desastre de los estilos ───────────────────────────────────────
    # GitHub Pages en modo «rama» compila con Jekyll 3, que usa libsass y no
    # entiende el `@use` de Dart Sass. En vez de fallar, publicaba el archivo
    # tal cual: 182 bytes de `@use` en crudo y el sitio entero sin un solo
    # estilo, sin ningún error en ninguna parte.

    @comprobar("El CSS está compilado, no es SCSS en crudo")
    def _():
        css = list((destino / "assets" / "css").glob("*.css"))
        if not css:
            return ["no hay ningún .css en assets/css/"]
        problemas = []
        for c in css:
            t = c.read_text(encoding="utf-8", errors="replace")
            if "@use" in t or "@import" in t:
                problemas.append(f"{c.name} todavía lleva @use/@import sin resolver")
            if len(t) < 10_000:
                problemas.append(f"{c.name} pesa {len(t)} bytes: demasiado poco para este sitio")
            if "$" in t and re.search(r"\$[a-z-]+\s*:", t):
                problemas.append(f"{c.name} tiene variables de Sass sin sustituir")
        return problemas

    @comprobar("El CSS trae la paleta y las tipografías")
    def _():
        css = list((destino / "assets" / "css").glob("*.css"))
        t = "".join(c.read_text(encoding="utf-8", errors="replace") for c in css)
        problemas = []
        if "--fondo" not in t or "--tinta" not in t:
            problemas.append("faltan las variables de color (--fondo, --tinta)")
        if t.count("@font-face") < 4:
            problemas.append(f"solo {t.count('@font-face')} @font-face; deberían ser muchos más")
        if '[data-tema="claro"]' not in t and "data-tema=claro" not in t:
            problemas.append("no aparece el modo claro en el CSS")
        return problemas

    # ── Recursos que no resuelven ────────────────────────────────────────
    # Un href a un archivo que no existe no da error en ningún sitio: el
    # navegador simplemente no pinta esa parte.

    @comprobar("Todos los recursos locales existen")
    def _():
        problemas = []
        patron = re.compile(r'(?:src|href)="(/[^"#?]+\.[a-z0-9]{2,5})(?:[?#][^"]*)?"', re.I)
        for pagina in paginas:
            html = pagina.read_text(encoding="utf-8", errors="replace")
            for ruta in set(patron.findall(html)):
                if not (destino / ruta.lstrip("/")).exists():
                    problemas.append(f"{pagina.relative_to(destino)} → {ruta}")
        return problemas

    @comprobar("Las tipografías del CSS existen")
    def _():
        problemas = []
        for c in (destino / "assets" / "css").glob("*.css"):
            t = c.read_text(encoding="utf-8", errors="replace")
            for u in set(re.findall(r'url\(["\']?(/[^)"\']+)["\']?\)', t)):
                if not (destino / u.lstrip("/")).exists():
                    problemas.append(f"{c.name} pide {u}, que no está")
        return problemas

    # ── La cadena vacía en Liquid ────────────────────────────────────────
    # En Liquid la cadena vacía es *verdadera*, así que `{% if algo %}` con
    # `algo: ""` entra en el bloque igual. Eso ponía un <img src=""> roto en
    # la ficha de autor de cada artículo.

    @comprobar("No hay atributos vacíos por la cadena vacía de Liquid")
    def _():
        problemas = []
        for pagina in paginas:
            html = pagina.read_text(encoding="utf-8", errors="replace")
            for attr in ("src", "href", "srcset"):
                if f'{attr}=""' in html:
                    problemas.append(
                        f'{pagina.relative_to(destino)} tiene un {attr}="" '
                        f"(¿un `if` sobre un valor vacío de _config.yml?)"
                    )
        return problemas

    # ── Liquid que se escapa al HTML ─────────────────────────────────────
    # Una llave mal cerrada no rompe la compilación: se imprime tal cual.

    @comprobar("No se ha escapado sintaxis de Liquid al HTML")
    def _():
        problemas = []
        for pagina in paginas:
            html = pagina.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r"\{\{[^}]{0,60}\}\}|\{%[^%]{0,60}%\}", html):
                problemas.append(f"{pagina.relative_to(destino)}: {m.group(0)[:50]}")
        return problemas

    # ── Los archivos que no son páginas ──────────────────────────────────
    # robots.txt salió una vez envuelto en la plantilla del sitio: 6.548
    # bytes de HTML donde debía haber cuatro líneas de texto. Google se lo
    # habría comido sin rechistar.

    @comprobar("robots.txt es texto, no una página")
    def _():
        r = destino / "robots.txt"
        if not r.exists():
            return ["no existe"]
        t = r.read_text(encoding="utf-8", errors="replace").lstrip()
        problemas = []
        if t.startswith("<") or "<html" in t.lower() or "<!doctype" in t.lower():
            problemas.append("le falta `layout: null`: ha salido envuelto en HTML")
        if "Sitemap:" not in t:
            problemas.append("no apunta al sitemap")
        return problemas

    @comprobar("El sitemap es XML bien formado")
    def _():
        s = destino / "sitemap.xml"
        if not s.exists():
            return ["no existe"]
        try:
            arbol = ElementTree.parse(s)
        except ElementTree.ParseError as e:
            return [f"no es XML válido: {e}"]
        urls = len(list(arbol.getroot()))
        return [] if urls else ["está vacío: no lista ni una URL"]

    @comprobar("El manifiesto es JSON válido")
    def _():
        import json
        m = destino / "manifiesto.webmanifest"
        if not m.exists():
            return ["no existe"]
        try:
            json.loads(m.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return [f"JSON roto: {e}"]
        return []

    # ── Que el sitio esté entero ─────────────────────────────────────────

    @comprobar("Cada sección de secciones.yml tiene su página")
    def _():
        texto = (RAIZ / "_data" / "secciones.yml").read_text(encoding="utf-8")
        urls = re.findall(r"^\s+url:\s*(\S+)", texto, re.M)
        problemas = []
        for u in urls:
            if not (destino / u.strip("/") / "index.html").exists():
                problemas.append(f"falta la página de {u}")
        return problemas

    @comprobar("Las páginas de siempre están donde deben")
    def _():
        obligatorias = ["index.html", "acerca/index.html", "trabajos/index.html", "404.html"]
        return [f"falta {p}" for p in obligatorias if not (destino / p).exists()]

    @comprobar("Toda página tiene título y descripción")
    def _():
        # Hay que sacar el contenido y mirar si tiene algo dentro. Comprobar
        # que detrás de `<title>` viene un carácter no vacío da por bueno un
        # `<title></title>`, porque el `<` del cierre ya cuenta.
        problemas = []
        for pagina in paginas:
            html = pagina.read_text(encoding="utf-8", errors="replace")
            rel = pagina.relative_to(destino)

            t = re.search(r"<title[^>]*>(.*?)</title>", html, re.S)
            if not t or not t.group(1).strip():
                problemas.append(f"{rel} sin <title> o con el título vacío")

            d = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', html)
            if not d or not d.group(1).strip():
                problemas.append(f"{rel} sin meta description o con ella vacía")
        return problemas

    # ── Lo que no debe salir nunca ───────────────────────────────────────
    # El encargo es explícito: ni un rastro de que esto lo haya tocado una
    # inteligencia artificial, en ninguna parte del blog ni de su proceso.

    @comprobar("Ni un rastro de IA en lo publicado")
    def _():
        prohibidas = [
            "claude", "anthropic", "chatgpt", "openai", "copilot",
            "co-authored-by", "generated with", "generado con ia",
            "as an ai", "language model",
        ]
        problemas = []
        for archivo in list(paginas) + list(destino.rglob("*.css")) + list(destino.rglob("*.js")) \
                + list(destino.rglob("*.xml")) + list(destino.rglob("*.txt")):
            t = archivo.read_text(encoding="utf-8", errors="replace").lower()
            for p in prohibidas:
                if p in t:
                    problemas.append(f"{archivo.relative_to(destino)} contiene «{p}»")
        return problemas

    @comprobar("No queda texto de relleno")
    def _():
        # Hay que mirar el texto que se lee, no el HTML en crudo. Buscando en
        # el HTML, un `placeholder="tu@correo.com"` —que es un atributo de
        # toda la vida— se contaba como relleno, y con los formularios de
        # comentarios y newsletter eso son todas las páginas del sitio.
        marcas = [
            "lorem ipsum", "pendiente:", "todo:", "texto de relleno",
            "placeholder", "xxxx", "sustitúyelo", "por determinar",
        ]
        problemas = []
        for pagina in paginas:
            t = _texto_visible(pagina.read_text(encoding="utf-8", errors="replace")).lower()
            for m in marcas:
                if m in t:
                    problemas.append(f"{pagina.relative_to(destino)} contiene «{m}»")
        return problemas

    # ── Lo que rompe la compilación en GitHub, no aquí ───────────────────
    # El Gemfile.lock se genera en Windows y lista solo la plataforma de
    # Windows. El runner de GitHub es Linux y se planta antes de empezar.

    @comprobar("Gemfile.lock sirve para el Linux de GitHub")
    def _():
        lock = RAIZ / "Gemfile.lock"
        if not lock.exists():
            return ["no existe, y tiene que estar versionado"]
        t = lock.read_text(encoding="utf-8", errors="replace")
        if "x86_64-linux" not in t:
            return [
                "no lista x86_64-linux: la compilación en GitHub fallará al "
                "preparar Ruby. Se arregla con:  bundle lock --add-platform x86_64-linux"
            ]
        return []

    # ── El código fuente que hay que copiar y pegar ──────────────────────
    # Las funciones de Supabase se pegan a mano en el editor de su panel, y
    # un byte de control no sobrevive a un copiar-pegar. Un \u0000 escrito
    # como carácter de verdad, en vez de como escape, cuela un NUL en el
    # archivo: git lo marca como binario, el editor lo tira, y la función
    # sube rota sin que nadie vea nada raro.

    @comprobar("Ningún archivo de texto lleva caracteres de control")
    def _():
        problemas = []
        patrones = ("*.ts", "*.js", "*.sql", "*.scss", "*.html", "*.yml", "*.md", "*.py")
        for patron in patrones:
            for archivo in RAIZ.rglob(patron):
                if "_site" in archivo.parts or ".git" in archivo.parts:
                    continue
                b = archivo.read_bytes()
                malos = {
                    x for x in b
                    if x < 9 or x in (11, 12) or 14 <= x <= 31 or x == 127
                }
                if malos:
                    nombres = ", ".join(f"0x{x:02x}" for x in sorted(malos))
                    problemas.append(
                        f"{archivo.relative_to(RAIZ)} lleva {nombres} de verdad; "
                        f"deberían estar escritos como escape (\\x00, \\x1F…)"
                    )
        return problemas

    # ── Avisos: cosas que mirar, no que paren nada ───────────────────────

    avisar("Imágenes que van a hacer lenta la página", [
        f"{p.relative_to(destino)} pesa {p.stat().st_size // 1024} KB"
        for p in destino.rglob("*")
        if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
        and p.stat().st_size > 400 * 1024
    ])

    avisar("Enlaces externos sin rel=noopener", [
        f"{pagina.relative_to(destino)}: {m[:60]}"
        for pagina in paginas
        for m in re.findall(r'<a [^>]*href="https?://[^"]+"[^>]*>', pagina.read_text(encoding="utf-8", errors="replace"))
        if 'target="_blank"' in m and "noopener" not in m
    ])

    # ── Resumen ──────────────────────────────────────────────────────────
    print()
    if fallos:
        print(f"  {len(fallos)} de {hechas} comprobaciones han fallado:")
        for f in fallos:
            print(f"    · {f}")
        print("\n  El sitio NO se publica. Arregla lo de arriba y vuelve a intentarlo.")
        return 1

    extra = f", {len(avisos)} aviso(s) que mirar sin prisa" if avisos else ""
    print(f"  Las {hechas} comprobaciones pasan{extra}. El sitio se puede publicar.")
    return 0


if __name__ == "__main__":
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "_site"
    raise SystemExit(main(destino.resolve()))
