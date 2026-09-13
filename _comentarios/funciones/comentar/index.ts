// Recibe un comentario del blog, lo guarda y avisa por correo.
//
// Es la única puerta de escritura de la tabla. El navegador del lector nunca
// escribe directamente: así la clave que va en el HTML del blog, que es
// pública, no sirve para nada más que para leer lo ya publicado.

import {
  AJUSTES, baseDeDatos, demasiados, enviarCorreo, escapar, firmar,
  huellaDe, limpiar, responder,
} from "../_compartido/comun.ts";

// Cuánto se aguanta de un mismo sitio antes de cortar.
const TOPE = 5;
const VENTANA = 10;         // minutos

// Un formulario que se envía en menos de esto no lo ha rellenado una
// persona: no da tiempo ni a leer los campos.
const SEGUNDOS_MINIMOS = 4;

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return responder(req, {}, 204);
  if (req.method !== "POST") return responder(req, { error: "Method not allowed" }, 405);

  let datos: Record<string, unknown>;
  try {
    datos = await req.json();
  } catch {
    return responder(req, { error: "No se entiende lo enviado." }, 400);
  }

  // ── Los dos filtros silenciosos ────────────────────────────────────────
  // A un robot no se le dice que se le ha pillado: se le responde que todo
  // ha ido bien y no se guarda nada. Si se le avisa, prueba otra cosa.

  if (limpiar(datos.web, 200)) {
    // Campo trampa, invisible en la página. Una persona no puede rellenarlo.
    return responder(req, { ok: true, id: null });
  }
  if (Number(datos.segundos) < SEGUNDOS_MINIMOS) {
    return responder(req, { ok: true, id: null });
  }

  // ── Lo que ha escrito ──────────────────────────────────────────────────

  const slug = limpiar(datos.slug, 120).toLowerCase();
  const apodo = limpiar(datos.apodo, 40);
  const texto = limpiar(datos.texto, 2000);
  const instagram = limpiar(datos.instagram, 30).replace(/^@+/, "").replace(/\/+$/, "");

  if (!/^[a-z0-9-]{1,120}$/.test(slug)) {
    return responder(req, { error: "No sé a qué entrada pertenece esto." }, 400);
  }
  if (apodo.length < 1) {
    return responder(req, { error: "Pon cómo quieres que te llame." }, 400);
  }
  if (texto.length < 2) {
    return responder(req, { error: "El comentario está vacío." }, 400);
  }
  // La dirección de la entrada, para poder ir a verla desde el correo. El
  // permalink es /año/mes/título/, así que no se puede reconstruir desde el
  // slug. Se acepta lo que manda el navegador, pero solo si apunta al blog:
  // si no, este correo sería un sitio cómodo desde el que colar un enlace.
  let donde = `${AJUSTES.sitio}/`;
  const propuesta = limpiar(datos.url, 300);
  if (propuesta.startsWith(AJUSTES.sitio + "/") && !propuesta.includes("..")) {
    donde = propuesta;
  }

  if (instagram && !/^[A-Za-z0-9._]{1,30}$/.test(instagram)) {
    return responder(req, {
      error: "Ese Instagram no parece un usuario. Solo el nombre, sin la arroba.",
    }, 400);
  }

  // ── ¿Viene demasiado seguido? ──────────────────────────────────────────

  const huella = await huellaDe(req);
  if (await demasiados("comentarios", huella, VENTANA, TOPE)) {
    return responder(req, {
      error: "Has escrito varios seguidos. Espera unos minutos y vuelve.",
    }, 429);
  }

  // ── Guardarlo ──────────────────────────────────────────────────────────

  const r = await baseDeDatos("comentarios", {
    method: "POST",
    preferir: "return=representation",
    body: JSON.stringify({
      slug, apodo, texto, huella,
      instagram: instagram || null,
    }),
  });

  if (!r.ok) {
    console.error("no se pudo guardar:", r.status, await r.text());
    return responder(req, { error: "No se ha podido guardar. Inténtalo en un rato." }, 500);
  }

  const [guardado] = await r.json();

  // ── Avisar, sin que el aviso pueda tumbar el comentario ────────────────
  // Si Resend está caído, el comentario ya está publicado y el lector ve su
  // mensaje. El correo es cosa nuestra, no suya.

  const firma = await firmar(`borrar:${guardado.id}`);
  const enlace = `${AJUSTES.url}/functions/v1/enlace` +
    `?que=borrar&id=${guardado.id}&firma=${firma}`;

  const ig = instagram
    ? `<a href="https://instagram.com/${escapar(instagram)}">@${escapar(instagram)}</a>`
    : "sin Instagram";

  await enviarCorreo(
    AJUSTES.avisos,
    `Comentario de ${apodo} en «${slug}»`,
    `<div style="font-family:Georgia,serif;line-height:1.6;max-width:34rem">
      <p style="color:#666;font-size:13px;letter-spacing:.1em;text-transform:uppercase">
        Nuevo comentario
      </p>
      <p><strong>${escapar(apodo)}</strong> · ${ig}</p>
      <blockquote style="margin:1rem 0;padding-left:1rem;border-left:3px solid #C2410C;
                         white-space:pre-wrap">${escapar(texto)}</blockquote>
      <p><a href="${escapar(donde)}#comentarios">Verlo en el blog</a></p>
      <p style="margin-top:2rem;font-size:14px">
        Ya está publicado. Si no debería estarlo:
        <a href="${enlace}" style="color:#991B1B">quitarlo del blog</a>.
      </p>
    </div>`,
  );

  return responder(req, {
    ok: true,
    comentario: {
      id: guardado.id,
      apodo: guardado.apodo,
      instagram: guardado.instagram,
      texto: guardado.texto,
      creado: guardado.creado,
    },
  });
});
