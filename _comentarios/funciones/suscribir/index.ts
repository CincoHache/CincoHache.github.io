// Apunta a alguien a la newsletter. En dos tiempos, a propósito.
//
// Nadie entra en la lista por escribir su correo en un formulario: entra
// cuando pincha el enlace del mensaje que le llega. Se llama doble
// confirmación y no es burocracia:
//
//   · Cualquiera puede escribir el correo de otro. Sin confirmar, apuntas a
//     gente que no ha pedido nada, que es la definición de spam.
//   · En España el RGPD pide poder demostrar el consentimiento. El clic en
//     el enlace, con su fecha, es esa prueba.
//   · Una lista sin confirmar se llena de direcciones falsas, y eso es lo
//     que hace que tus envíos acaben en la carpeta de spam de todos.

import {
  AJUSTES, baseDeDatos, demasiados, enviarCorreo, escapar, firmar,
  huellaDe, limpiar, responder,
} from "../_compartido/comun.ts";

const TOPE = 3;
const VENTANA = 60;          // minutos
const SEGUNDOS_MINIMOS = 2;

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return responder(req, {}, 204);
  if (req.method !== "POST") return responder(req, { error: "Method not allowed" }, 405);

  let datos: Record<string, unknown>;
  try {
    datos = await req.json();
  } catch {
    return responder(req, { error: "No se entiende lo enviado." }, 400);
  }

  if (limpiar(datos.web, 200)) return responder(req, { ok: true });
  if (Number(datos.segundos) < SEGUNDOS_MINIMOS) return responder(req, { ok: true });

  const correo = limpiar(datos.correo, 254).toLowerCase();
  const origen = limpiar(datos.origen, 200);

  if (!/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(correo)) {
    return responder(req, { error: "Ese correo no parece un correo." }, 400);
  }

  const huella = await huellaDe(req);
  if (await demasiados("suscriptores", huella, VENTANA, TOPE)) {
    return responder(req, {
      error: "Demasiados intentos. Prueba dentro de un rato.",
    }, 429);
  }

  // ── ¿Ya estaba? ────────────────────────────────────────────────────────
  // Aquí hay que tener cuidado con lo que se responde. Si dijéramos «este
  // correo ya está apuntado», cualquiera podría averiguar quién está en la
  // lista probando direcciones. Así que la respuesta es siempre la misma.

  const consulta = await baseDeDatos(
    `suscriptores?correo=eq.${encodeURIComponent(correo)}&select=id,estado,ficha`,
  );
  const [existente] = consulta.ok ? await consulta.json() : [];

  const MISMA_RESPUESTA = {
    ok: true,
    mensaje: "Te hemos mandado un correo. Pincha el enlace y ya estás dentro.",
  };

  if (existente?.estado === "confirmado") {
    // Ya estaba dentro. No se manda nada y se responde igual que siempre.
    return responder(req, MISMA_RESPUESTA);
  }

  let ficha: string;
  let id: string;

  if (existente) {
    // Se apuntó y no confirmó, o se dio de baja y vuelve. Se reaprovecha la
    // fila y se le manda otra vez el enlace.
    ficha = existente.ficha;
    id = existente.id;
    await baseDeDatos(`suscriptores?id=eq.${id}`, {
      method: "PATCH",
      body: JSON.stringify({ estado: "pendiente", creado: new Date().toISOString(), huella }),
    });
  } else {
    ficha = crypto.randomUUID().replace(/-/g, "");
    const r = await baseDeDatos("suscriptores", {
      method: "POST",
      preferir: "return=representation",
      body: JSON.stringify({ correo, ficha, huella, origen: origen || null }),
    });
    if (!r.ok) {
      console.error("no se pudo apuntar:", r.status, await r.text());
      return responder(req, { error: "No se ha podido apuntar. Inténtalo en un rato." }, 500);
    }
    [{ id }] = await r.json();
  }

  // ── El correo de confirmación ──────────────────────────────────────────

  const firmaConfirmar = await firmar(`confirmar:${ficha}`);
  const firmaBaja = await firmar(`baja:${ficha}`);
  const base = `${AJUSTES.url}/functions/v1/enlace`;

  const enviado = await enviarCorreo(
    correo,
    "Confirma tu suscripción a Cinco Hache",
    `<div style="font-family:Georgia,serif;line-height:1.7;max-width:34rem;color:#14120F">
      <p style="font-size:12px;letter-spacing:.22em;text-transform:uppercase;color:#8A8172">
        Cinco Hache
      </p>
      <p>Alguien ha pedido recibir lo que se publique en Cinco Hache en esta
         dirección. Si has sido tú, confírmalo:</p>
      <p style="margin:2rem 0">
        <a href="${base}?que=confirmar&ficha=${ficha}&firma=${firmaConfirmar}"
           style="background:#C2410C;color:#fff;padding:.8rem 1.6rem;
                  text-decoration:none;border-radius:2px">Sí, apúntame</a>
      </p>
      <p style="color:#4A4437;font-size:15px">
         Si no has sido tú, no hagas nada: sin este clic no entras en ninguna
         lista y este correo es el último que recibes.</p>
      <p style="color:#8A8172;font-size:13px;margin-top:2.5rem">
         Para no recibir nada nunca más, ni siquiera esto:
         <a href="${base}?que=baja&ficha=${ficha}&firma=${firmaBaja}"
            style="color:#8A8172">darse de baja</a>.</p>
    </div>`,
  );

  if (!enviado) {
    console.error("no se pudo enviar la confirmación a", escapar(correo));
    return responder(req, {
      error: "No hemos podido mandarte el correo de confirmación. Inténtalo más tarde.",
    }, 502);
  }

  return responder(req, MISMA_RESPUESTA);
});
