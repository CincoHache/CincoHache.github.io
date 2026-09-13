# Comentarios y newsletter — puesta en marcha

Media hora, dos cuentas gratis y ningún dato de tarjeta. Mientras no hagas
esto, el blog funciona exactamente igual que ahora: sin formularios y sin
errores, porque los dos bloques solo se pintan cuando hay configuración.

Hay dos cuentas porque hacen cosas distintas:

| | Para qué | Coste |
|---|---|---|
| **Supabase** | Guardar los comentarios y la lista de correos | Gratis. El plan libre da de sobra para un blog |
| **Resend** | Mandar los avisos y las confirmaciones | Gratis hasta 3.000 correos al mes |

---

## 1 · Supabase

1. **supabase.com** → *Start your project* → entra con GitHub.
2. *New project*. Nombre: `cinco-hache`. Región: **West EU (Ireland)**, que es
   la más cercana. Te pide una contraseña para la base de datos: guárdala en
   tu gestor, aunque no la vas a usar casi nunca.
3. Tarda un par de minutos en crearse.

### La estructura

Panel del proyecto → **SQL Editor** → *New query* → pega entero el contenido
de [`esquema.sql`](esquema.sql) → **Run**.

Tiene que salir una fila que dice `listo`. Se puede volver a ejecutar las
veces que quieras: no borra nada de lo que ya haya.

### Las dos claves

**Project Settings → API**. Copia:

- **Project URL** → va en `_config.yml`, en `supabase: url:`
- **anon public** → va en `supabase: clave:`

> Esa clave es **pública a propósito**. Va en el HTML del blog y la ve
> cualquiera con el botón derecho. No pasa nada: con ella solo se pueden
> *leer* comentarios ya publicados. Escribir se escribe por otra puerta.
>
> La otra clave, la **service_role**, es la que abre todo. Esa no sale nunca
> del panel de Supabase. Si alguna vez la pegas en el blog por error,
> vuelve a Settings → API → *Generate new key* y cámbiala.

---

## 2 · Resend

1. **resend.com** → *Sign up*. **Date de alta con `cincohache@yahoo.com`**,
   que es a donde van a llegar los avisos.
2. *API Keys* → *Create API Key*. Permiso: **Sending access**. Cópiala: solo
   se enseña una vez.

> En el plan gratis y sin dominio propio, Resend **solo te deja mandar a la
> dirección con la que te diste de alta**. Para los avisos de comentarios
> vale perfectamente, porque son para ti.
>
> **Para la newsletter no basta**: los correos de confirmación van a
> desconocidos. Cuando quieras abrirla de verdad, hay que verificar un
> dominio en Resend → *Domains*. Un dominio cuesta unos 10 € al año y además
> te quita el `.github.io` de la dirección del blog. Hasta entonces, la
> newsletter recoge suscripciones tuyas de prueba pero no confirmará las de
> nadie más.

---

## 3 · Las tres funciones

Panel → **Edge Functions** → *Deploy a new function* → *Via Editor*.

Hay que crear tres, con estos nombres exactos:

| Nombre | Archivo que se pega |
|---|---|
| `comentar` | [`funciones/comentar/index.ts`](funciones/comentar/index.ts) |
| `suscribir` | [`funciones/suscribir/index.ts`](funciones/suscribir/index.ts) |
| `enlace` | [`funciones/enlace/index.ts`](funciones/enlace/index.ts) |

Las tres empiezan con `import … from "../_compartido/comun.ts"`. Desde el
editor del navegador no hay carpeta compartida, así que en cada una hay que
**pegar arriba el contenido de [`funciones/_compartido/comun.ts`](funciones/_compartido/comun.ts)
y borrar esa línea de `import`**. Es fea pero es una vez.

*(Si algún día instalas la herramienta de línea de comandos de Supabase,
`supabase functions deploy` sube las tres respetando la carpeta compartida y
esto sobra.)*

### Los secretos

Panel → **Edge Functions → Secrets** → *Add new secret*. Cinco:

| Nombre | Valor |
|---|---|
| `FIRMA_SECRETO` | Una frase larga que te inventes. Firma los enlaces de los correos |
| `RESEND_API_KEY` | La de Resend |
| `CORREO_AVISOS` | `cincohache@yahoo.com` |
| `REMITENTE` | `Cinco Hache <onboarding@resend.dev>` |
| `SITIO` | `https://cincohache.github.io` |

Para `FIRMA_SECRETO` vale cualquier cosa larga e irrepetible. **Si la cambias
después, los enlaces de los correos ya enviados dejan de funcionar** — los de
baja incluidos, así que mejor no tocarla.

`SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` no hay que ponerlas: Supabase se
las pasa solo a sus funciones.

---

## 4 · Encenderlo

En `_config.yml`, rellena las dos líneas:

```yaml
supabase:
  url: "https://xxxxxxxxxxxx.supabase.co"
  clave: "eyJhbGciOi…"
```

Doble clic en `revisar.cmd` para comprobar que todo compila, y sube. En
cuanto esté desplegado, los comentarios salen al final de cada entrada y la
newsletter en el pie de todas las páginas.

---

## Cómo funciona, en cuatro líneas

```
   El lector escribe
         ↓
   función «comentar»        ← valida, frena robots, guarda
         ↓                      y te manda el aviso
   base de datos             ← aquí vive
         ↓
   el blog lo lee            ← con la clave pública, solo lectura
```

**El navegador nunca escribe en la base de datos.** Por eso la clave del
blog puede ser pública sin que importe.

## Contra los robots

Cuatro cosas, ninguna molesta a nadie:

- Un campo **trampa**, invisible en la página y fuera del tabulador. Una
  persona no puede rellenarlo; los robots rellenan todo lo que encuentran.
- Un **mínimo de segundos** desde que se ve el formulario hasta que se envía.
- Un **tope por sitio**: cinco comentarios cada diez minutos, tres
  suscripciones por hora.
- **Límites en la propia base de datos**, no solo en el formulario. Un
  formulario se salta con dos líneas de consola; una restricción de Postgres
  no.

A los robots no se les avisa de que se les ha pillado: se les responde que
todo ha ido bien y no se guarda nada. Si se les avisa, prueban otra cosa.

## El día a día

**Un comentario que no debería estar.** Te llega el aviso a Yahoo con el
texto y un enlace de *quitarlo del blog*. Un clic. No se borra: se esconde,
por si acaso.

**Ver la lista de correos.** Panel → SQL Editor → `select * from envio;` →
*Download CSV*. Ese archivo se sube a cualquier servicio de envío el día que
quieras mandar algo.

**Apagarlo todo.** En `_config.yml`, `activos: false` o `activa: false`. Los
bloques desaparecen y no se pierde nada de lo guardado.
