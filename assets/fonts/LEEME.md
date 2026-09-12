# Fuentes de Cinco Hache

Dos familias, las dos de [Google Fonts](https://fonts.google.com/) y las dos con
licencia OFL, así que se pueden servir desde el propio sitio sin pedir permiso a
nadie.

| Papel | Familia | Variable CSS |
|---|---|---|
| Titulares | **Bodoni Moda** | `--f-titular` |
| Cuerpo | **Literata** | `--f-texto` |
| Rótulos, fechas, menú, pies | **Literata**, en versalita falsa | `--f-detalle` |

Bodoni Moda es una didona de alto contraste: es la que casa con el blackletter
del logo y da el aire de cabecera de periódico. Literata está dibujada para leer
largo en pantalla, con más peso en los trazos finos que una didona, y aguanta
bien tanto el cuerpo del artículo como los rótulos en mayúsculas pequeñas.

## Los archivos

```
ch-titular.woff2                 46 KB   Bodoni Moda, latin
ch-titular-ext.woff2             25 KB   Bodoni Moda, latin-ext
ch-titular-italica.woff2         54 KB
ch-titular-italica-ext.woff2     28 KB
ch-texto.woff2                   86 KB   Literata, latin
ch-texto-ext.woff2               71 KB   Literata, latin-ext
ch-texto-italica.woff2           89 KB
ch-texto-italica-ext.woff2       71 KB
```

Son **fuentes variables**: cada archivo cubre de 400 a 700 y todo el eje óptico,
en vez de necesitar uno por grosor. Y van partidas por subconjunto de caracteres
con su `unicode-range`, así que el navegador solo baja lo que la página usa de
verdad: un artículo en castellano sin cursivas se lleva unos 130 KB, no los 470
que suman todos.

El castellano entra entero en `latin` —tildes, eñe, diéresis, signos de apertura
y comillas latinas—. `latin-ext` solo se descarga si aparece algún carácter raro.

## Cambiarlas

1. Elige las nuevas. Si son de Google Fonts o de
   [Fontshare](https://www.fontshare.com/), la licencia ya permite uso web. Una
   fuente comercial necesita licencia **web** específica: la de escritorio no la
   cubre.
2. Descarga los `.woff2` con
   [google-webfonts-helper](https://gwfh.mranftl.com/fonts).
3. Renómbralos con los nombres de arriba y déjalos aquí.
4. Si cambian los `unicode-range`, actualízalos en `_sass/_tipografia.scss`.
5. Reinicia el servidor.

Para volver a la pila del sistema sin borrar nada, pon la primera línea de
`_sass/_tipografia.scss` en `false`.

## Y en Google Docs

Las dos están en el catálogo de Google Fonts, así que la plantilla de Docs puede
usar exactamente las mismas: menú de fuentes → **Más fuentes** → buscar «Bodoni
Moda» y «Literata». Es lo más cerca que van a quedar el documento y el blog.

Las medidas concretas para cada estilo están en
`herramienta/PLANTILLA-GOOGLE-DOCS.md`, apartado 4.2.

## Marca

El logo no necesita nada de esto: los PNG de `assets/img/marca/` ya llevan el
texto convertido a curvas. Las fuentes originales del logotipo son
**UnifrakturMaguntia** (el 5) y **Pirata One** (la H), ambas de Google Fonts, por
si alguna vez hay que reconstruirlo.
