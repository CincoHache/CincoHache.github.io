// Todo lo que se pincha desde un correo pasa por aquí.
//
//   ?que=borrar     &id=<uuid>  &firma=…   quitar un comentario del blog
//   ?que=confirmar  &ficha=<…>  &firma=…   entrar en la newsletter
//   ?que=baja       &ficha=<…>  &firma=…   salir de la newsletter
//
// Una sola función para las tres cosas, con una sola forma de firmar. Tres
// funciones distintas serían tres sitios donde equivocarse con lo mismo.
//
// La firma es lo único que autoriza. Sin ella, quien adivinara un
// identificador podría borrar comentarios ajenos o dar de baja a cualquiera,
// y los identificadores viajan a la vista en un correo.

import {
  baseDeDatos, firmaValida, limpiar, pagina,
} from "../_compartido/comun.ts";

Deno.serve(async (req) => {
  const url = new URL(req.url);
  const que = limpiar(url.searchParams.get("que"), 20);
  const firma = limpiar(url.searchParams.get("firma"), 60);
  const id = limpiar(url.searchParams.get("id"), 40);
  const ficha = limpiar(url.searchParams.get("ficha"), 40);

  const referencia = que === "borrar" ? id : ficha;
  if (!que || !firma || !referencia) {
    return pagina("Enlace incompleto", "A este enlace le falta algo. Vuelve a copiarlo entero desde el correo.");
  }

  if (!await firmaValida(`${que}:${referencia}`, firma)) {
    return pagina(
      "Este enlace no vale",
      "La firma no cuadra. O el enlace se ha cortado al copiarlo, o no venía de un correo nuestro.",
    );
  }

  // ── Quitar un comentario ───────────────────────────────────────────────
  // No se borra: se esconde. Si un día resulta que no había por qué
  // quitarlo, está ahí para volver a ponerlo. Y si era spam, da igual.

  if (que === "borrar") {
    const r = await baseDeDatos(`comentarios?id=eq.${id}`, {
      method: "PATCH",
      preferir: "return=representation",
      body: JSON.stringify({ visible: false }),
    });
    const filas = r.ok ? await r.json() : [];
    if (!filas.length) {
      return pagina("Ya no estaba", "Ese comentario ya se había quitado antes, o no existe.");
    }
    return pagina(
      "Quitado",
      "El comentario ya no se ve en el blog. No se ha borrado del todo: sigue en la " +
      "base de datos por si hubiera que volver a ponerlo.",
    );
  }

  // ── Entrar en la newsletter ────────────────────────────────────────────

  if (que === "confirmar") {
    const r = await baseDeDatos(`suscriptores?ficha=eq.${ficha}`, {
      method: "PATCH",
      preferir: "return=representation",
      body: JSON.stringify({ estado: "confirmado", confirmado: new Date().toISOString(), baja_en: null }),
    });
    const filas = r.ok ? await r.json() : [];
    if (!filas.length) {
      return pagina("No encontramos esa suscripción", "Puede que se borrara hace tiempo. Vuelve a apuntarte desde el blog.");
    }
    return pagina(
      "Ya estás dentro",
      "Te llegará lo que se publique. Nada más: ni resúmenes, ni recordatorios, " +
      "ni tu correo en manos de nadie.",
    );
  }

  // ── Salir de la newsletter ─────────────────────────────────────────────
  // Sin preguntar dos veces, sin «¿seguro?», sin formularios. Un clic y
  // fuera: es lo que uno espera y es lo que manda la ley.

  if (que === "baja") {
    const r = await baseDeDatos(`suscriptores?ficha=eq.${ficha}`, {
      method: "PATCH",
      preferir: "return=representation",
      body: JSON.stringify({ estado: "baja", baja_en: new Date().toISOString() }),
    });
    const filas = r.ok ? await r.json() : [];
    if (!filas.length) {
      return pagina("No estabas apuntado", "No hemos encontrado esa suscripción. En cualquier caso, no recibirás nada.");
    }
    return pagina(
      "Te hemos dado de baja",
      "No recibirás nada más. Si alguna vez cambias de idea, el formulario sigue " +
      "en el pie del blog.",
    );
  }

  return pagina("No sé qué hacer con esto", "Ese enlace pide algo que no existe.");
});
