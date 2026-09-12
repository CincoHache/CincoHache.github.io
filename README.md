# Cinco Hache — el blog

Sitio estático hecho con [Jekyll](https://jekyllrb.com/) y publicado en GitHub
Pages. Esta es la **vertiente A** del proyecto. La herramienta que convierte los
documentos de Google Docs vive en un repositorio aparte (`../herramienta`), a
propósito: son dos proyectos distintos y GitHub Pages solo debe ver este.

El diseño sale del canvas de dirección de arte del proyecto; la paleta y la
marca, del logotipo 5H.

---

## Arrancar en local

```bash
bundle install                            # solo la primera vez
bundle exec jekyll serve --livereload
```

Luego, [http://localhost:4000](http://localhost:4000). Lo que ves ahí **es
exactamente** lo que se publicará: mismo motor, mismo resultado.

Los cambios en `_config.yml` **no** se recargan en caliente.

---

## Las cuatro secciones

Están en `_data/secciones.yml`, por orden de peso editorial. De ahí salen el
menú del pie, las páginas de sección, los filtros del archivo y la lista que
usa la herramienta de publicación.

| Sección | `categoria:` | Qué es |
|---|---|---|
| Ensayo | `ensayo` | Pensar despacio algo que no se resuelve en una tarde |
| Artículo de opinión | `opinion` | Lo que hay que decir cuando hay que decirlo |
| Proyecto | `proyecto` | Encargos y trabajo propio. Sale en «Trabajo seleccionado» |
| Otros | `otros` | Reseñas, fotoreportajes, diario y lo que no cabe en otro sitio |

`genero:` afina una entrada dentro de su sección —«Reseña» dentro de «Otros»—
y es lo que se enseña como rótulo, porque «Reseña» dice más que «Otros».

---

## Las cuatro aperturas

Se eligen con `apertura:` en el front matter.

| Valor | Qué hace |
|---|---|
| `ninguna` | Solo texto. Lo normal en una nota breve o una opinión |
| `plana` | La foto en 21:9 debajo del titular. La más segura |
| `mezcla` | El titular atraviesa la foto en modo diferencia. Pide una imagen monocroma y contrastada |
| `sangre` | La foto de borde a borde con el titular encima |

Sin `imagen_portada`, cualquiera de las tres últimas cae en `ninguna`.

---

## Mapa del repositorio

```
blog/
├── _config.yml            Configuración global, autoría y SEO.
├── Gemfile                Dependencias de Ruby.
├── .github/workflows/
│   └── jekyll.yml         Construye y publica en cada push a main.
│
├── _data/
│   ├── secciones.yml   ★  Las cuatro secciones. De aquí sale todo.
│   ├── sobre.yml       ★  El contenido de la página «Sobre mí».
│   └── es.yml             Nombres de mes y cadenas en español.
│
├── _layouts/
│   ├── default.html       Esqueleto: head, cabecera, pie.
│   ├── post.html          El artículo, con sus cuatro aperturas.
│   ├── seccion.html       Listado de una sección.
│   └── pagina.html        Páginas sueltas.
│
├── _includes/
│   ├── head.html          Metadatos, favicon, precargas, tema.
│   ├── cabecera.html      Marca, menú, buscar y el interruptor de tema.
│   ├── pie.html           Pie de página.
│   ├── sello.html         El rótulo de cabeza: sección / tema / minutos.
│   ├── entrega.html       El número de entrega de una entrada.
│   ├── sumario.html       El sumario lateral, sacado de los ladillos.
│   ├── fuentes.html    ★  El bloque plegable de fuentes.
│   ├── figura.html     ★  Imagen con pie. La escribe la herramienta.
│   ├── fila-archivo.html  Una fila del archivo, con datos para el buscador.
│   ├── pieza.html         Tarjeta de «Sigue leyendo».
│   └── fecha.html         Fechas en español.
│
├── _sass/              ★  Estilos. Empieza por _variables.scss.
│   ├── _variables.scss    Paleta, medidas y los dos temas.
│   ├── _fuentes.scss      Los @font-face. Se genera solo.
│   ├── _tipografia.scss   Las cuatro familias y la escala.
│   └── …
│
├── assets/
│   ├── css/main.scss      Punto de entrada del CSS.
│   ├── js/sitio.js        Tema, buscador, sumario y compartir.
│   ├── fonts/             Las cuatro familias, autoalojadas.
│   └── img/
│       ├── marca/         El logo 5H en todos sus tamaños.
│       └── marcador/      Imágenes de relleno. Borrar al publicar de verdad.
│
├── _posts/             ★  Las entradas publicadas.
├── _drafts/               Borradores. No se publican salvo con --drafts.
│
├── index.html             Portada.
├── trabajos.html          El archivo, con buscador y filtros.
├── ensayo.html            Páginas de sección: solo front matter.
├── opinion.html
├── proyecto.html
├── otros.html
├── acerca.html            Sobre mí.
├── 404.html
├── robots.txt
├── manifiesto.webmanifest
└── favicon.ico
```

Lo marcado con ★ es lo que se toca a menudo.

---

## El front matter

```yaml
---
layout: post
title: "El hueco que vendimos"
subtitle: "Entradilla, opcional"
date: 2026-09-11 09:00:00 +0200
categoria: ensayo              # ensayo | opinion | proyecto | otros
genero: "Reseña"               # opcional; afina dentro de la sección
tema: "Atención y tecnología"  # opcional; sale en el rótulo de cabeza
apertura: plana                # ninguna | plana | mezcla | sangre
imagen_portada: /assets/img/slug/01.jpg
image: /assets/img/slug/01.jpg # lo lee jekyll-seo-tag para redes
etiquetas: [atención, ciudad]
fuentes:
  - cita: "La cifra de 40.000 viajeros diarios"
    donde: "Memoria anual de Renfe, 2025"
    url: "https://…"
---
```

| Campo | Obligatorio | Qué hace |
|---|---|---|
| `layout` · `title` · `date` · `categoria` | Sí | Lo mínimo |
| `subtitle` | No | Entradilla |
| `genero` · `tema` | No | Afinan el rótulo de cabeza |
| `apertura` | No | Por defecto, `plana` si hay imagen |
| `etiquetas` | No | Píldoras al pie del artículo, enlazadas al buscador |
| `fuentes` | No | El bloque plegable. Lo escribe la herramienta |
| `entrega` | No | Fija el número de entrega; si falta, se cuenta |
| `capitular: false` | No | Quita la letra capital del primer párrafo |

---

## Lo que se rellena solo

Publicar una entrada la coloca en la portada, en su página de sección, en el
archivo con buscador, en el RSS, en el sitemap y en «Sigue leyendo» de las
entradas vecinas. No hay que archivar ni reordenar nada.

---

## Los dos temas

El interruptor de la cabecera cambia entre oscuro y claro y recuerda la
elección en el navegador. No es una inversión: son las dos mitades de la marca,
con su propia paleta cada una y su propia versión del logotipo.

El tema se aplica antes de pintar nada, con un fragmento en el `<head>`, para
que no haya un fogonazo del color contrario en cada página.

---

## Ajustar el diseño

Casi todo vive en dos archivos:

- `_sass/_variables.scss` — paleta, espaciado, anchos, los dos temas.
- `_sass/_tipografia.scss` — las cuatro familias y la escala.

Los componentes nunca usan un color directamente: usan un papel
(`--fondo`, `--tinta`, `--acento`, `--linea`…). Cambiar el tono del sitio
entero es cambiar unas pocas líneas.

---

## SEO

- `jekyll-seo-tag` genera título, descripción, canónica, Open Graph, tarjeta de
  Twitter y JSON-LD de tipo `Article`.
- Cada entrada lleva `image:`, que es lo que se ve al compartir el enlace.
- `jekyll-sitemap` y `jekyll-feed` mantienen `sitemap.xml` y `feed.xml`.
- `robots.txt` deja indexar todo menos la página de error y apunta al sitemap.
- Hay página por sección, además del archivo con filtros, para que los
  buscadores tengan algo que indexar sin depender de que alguien pulse un botón.
- Las fuentes se precargan; el logotipo también.
- No hay rastreadores, ni cookies, ni analítica.

---

## Publicar

```bash
git add .
git commit -m "Nuevo ensayo: El hueco que vendimos"
git push
```

Y luego, pestaña **Actions**: círculo verde, publicado. Entre uno y tres
minutos, más la caché del navegador.

Lo habitual es que esto lo haga la herramienta.

---

## Pendientes

- [ ] Rellenar `_data/sobre.yml` con tu texto.
- [ ] Correo y redes en `_config.yml`.
- [ ] Borrar las entradas de prueba (`marcador: true`) y `assets/img/marcador/`.
