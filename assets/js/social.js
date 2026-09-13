---
layout: null
---
/* Comentarios y newsletter.
 *
 * Las dos cosas hablan con el mismo sitio y se parecen tanto que separarlas
 * sería repetir el mismo código dos veces.
 *
 * La regla que manda sobre todas las demás: **si algo de aquí falla, el
 * artículo se lee igual**. No hay una sola línea que pueda dejar la página a
 * medias. Si Supabase está caído, si la clave está mal, si el lector tiene
 * el JavaScript apagado o se le corta la conexión a la mitad, lo que ve es
 * el texto entero y bien. Un blog es para leer; lo de comentar viene
 * después, y si no puede ser, no puede ser.
 */

(function () {
  "use strict";

  var API = {
    url: {{ site.supabase.url | jsonify }},
    clave: {{ site.supabase.clave | jsonify }}
  };
  if (!API.url || !API.clave) return;

  var FUNCIONES = API.url.replace(/\/$/, "") + "/functions/v1";

  /* ── Utilidades ──────────────────────────────────────────────────── */

  function $(sel, raiz) { return (raiz || document).querySelector(sel); }

  function texto(el, t) { el.textContent = t; }

  function avisar(caja, mensaje, malo) {
    var a = $("[data-aviso]", caja);
    if (!a) return;
    texto(a, mensaje);
    a.hidden = !mensaje;
    a.classList.toggle("es-error", !!malo);
  }

  /* Nada de innerHTML con texto de nadie: se construyen los nodos. Es la
   * diferencia entre un comentario y un comentario que ejecuta código. */
  function nodo(etiqueta, clase, contenido) {
    var el = document.createElement(etiqueta);
    if (clase) el.className = clase;
    if (contenido != null) el.textContent = contenido;
    return el;
  }

  function cuandoSea(fecha) {
    var d = new Date(fecha);
    if (isNaN(d)) return "";
    return d.toLocaleDateString("es-ES", { day: "numeric", month: "long", year: "numeric" });
  }

  /* Cuánto lleva el formulario a la vista. Un envío instantáneo no lo ha
   * hecho una persona, y es el filtro que más spam para sin molestar a
   * nadie: quien escribe de verdad tarda bastante más que esto. */
  function cronometro(forma) {
    var desde = Date.now();
    return function () { return Math.round((Date.now() - desde) / 1000); };
  }

  function recoger(forma) {
    var datos = {};
    Array.prototype.forEach.call(forma.elements, function (el) {
      if (el.name) datos[el.name] = el.value;
    });
    return datos;
  }

  function enviando(forma, si) {
    var boton = $("[data-enviar]", forma);
    if (!boton) return;
    boton.disabled = si;
    boton.classList.toggle("esta-cargando", si);
  }

  /* Un mensaje se le enseña al lector solo si lo hemos escrito nosotros.
   * Los del navegador —«Failed to fetch», «NetworkError»— son en inglés, no
   * dicen nada y asustan. Que no haya red no es culpa de quien comenta. */
  function mio(mensaje) {
    var e = new Error(mensaje);
    e.nuestro = true;
    return e;
  }

  function loQueDecir(err, porDefecto) {
    return (err && err.nuestro && err.message) ? err.message : porDefecto;
  }

  function llamar(funcion, cuerpo) {
    return fetch(FUNCIONES + "/" + funcion, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        apikey: API.clave,
        Authorization: "Bearer " + API.clave
      },
      body: JSON.stringify(cuerpo)
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (d) {
        if (!r.ok) throw mio(d.error || "No se ha podido enviar.");
        return d;
      });
    });
  }

  /* ── Comentarios ─────────────────────────────────────────────────── */

  var caja = $("[data-comentarios]");
  if (caja) montarComentarios(caja);

  function montarComentarios(caja) {
    var slug = caja.getAttribute("data-slug") || "";
    var lista = $("[data-lista]", caja);
    var estado = $("[data-estado]", caja);
    var cuenta = $("[data-cuenta]", caja);
    var forma = $("[data-formulario]", caja);
    var segundos = cronometro(forma);

    pintarRestantes();

    /* Traer lo que ya hay. Si falla, el bloque se retira entero en vez de
     * dejar un error puesto donde debería haber una conversación. */
    fetch(
      API.url + "/rest/v1/comentarios_publicos?slug=eq." +
      encodeURIComponent(slug) + "&select=id,apodo,instagram,texto,creado&order=creado.asc",
      { headers: { apikey: API.clave, Authorization: "Bearer " + API.clave } }
    )
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (filas) {
        estado.hidden = true;
        filas.forEach(function (c) { lista.appendChild(pintarComentario(c)); });
        actualizarCuenta(filas.length);
      })
      .catch(function () {
        /* Ni un mensaje de error: el formulario sigue ahí y funciona. Si de
         * verdad está todo caído, ya lo dirá al intentar enviar. */
        estado.hidden = true;
      });

    function actualizarCuenta(n) {
      if (!cuenta) return;
      texto(cuenta, n === 0 ? "" : n === 1 ? "1 comentario" : n + " comentarios");
      cuenta.hidden = n === 0;
    }

    function pintarRestantes() {
      var area = forma.elements.texto;
      var marca = $("[data-restantes]", forma);
      if (!area || !marca) return;
      area.addEventListener("input", function () {
        var quedan = 2000 - area.value.length;
        texto(marca, quedan < 200 ? quedan + " caracteres" : "");
      });
    }

    function pintarComentario(c) {
      var li = nodo("li", "comentario");

      var cabecera = nodo("div", "comentario__cabecera");
      if (c.instagram) {
        var a = nodo("a", "comentario__quien comentario__quien--enlace", c.apodo);
        a.href = "https://instagram.com/" + encodeURIComponent(c.instagram);
        a.rel = "nofollow noopener ugc";
        a.target = "_blank";
        a.title = "@" + c.instagram + " en Instagram";
        cabecera.appendChild(a);
      } else {
        cabecera.appendChild(nodo("span", "comentario__quien", c.apodo));
      }
      cabecera.appendChild(nodo("time", "comentario__cuando", cuandoSea(c.creado)));

      li.appendChild(cabecera);
      li.appendChild(nodo("p", "comentario__texto", c.texto));
      return li;
    }

    forma.addEventListener("submit", function (e) {
      e.preventDefault();
      var datos = recoger(forma);

      if (!datos.apodo.trim()) return avisar(caja, "Pon cómo quieres que te llame.", true);
      if (datos.texto.trim().length < 2) return avisar(caja, "El comentario está vacío.", true);

      enviando(forma, true);
      avisar(caja, "");

      llamar("comentar", {
        slug: slug,
        url: location.origin + location.pathname,
        apodo: datos.apodo,
        instagram: datos.instagram,
        texto: datos.texto,
        web: datos.web,
        segundos: segundos()
      })
        .then(function (d) {
          forma.reset();
          if (d.comentario) {
            lista.appendChild(pintarComentario(d.comentario));
            actualizarCuenta(lista.children.length);
          }
          avisar(caja, "Publicado. Gracias.");
        })
        .catch(function (err) {
          avisar(caja, loQueDecir(err,
            "No se ha podido enviar. Puede ser tu conexión. " +
            "Lo que has escrito sigue aquí: vuelve a darle en un momento."), true);
        })
        .then(function () { enviando(forma, false); });
    });
  }

  /* ── Newsletter ──────────────────────────────────────────────────── */

  var boletin = $("[data-newsletter]");
  if (boletin) montarBoletin(boletin);

  function montarBoletin(caja) {
    var forma = $("[data-formulario]", caja);
    var segundos = cronometro(forma);

    /* La casilla del pie lleva aquí y deja el cursor puesto: un ancla que
     * solo baja obliga a buscar el campo con el ratón. */
    var atajo = $("[data-ir-al-boletin]");
    if (atajo) {
      atajo.addEventListener("click", function () {
        setTimeout(function () {
          var campo = forma.elements.correo;
          if (campo) campo.focus({ preventScroll: true });
        }, 400);
      });
    }

    forma.addEventListener("submit", function (e) {
      e.preventDefault();
      var datos = recoger(forma);

      if (!/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(datos.correo.trim())) {
        return avisar(caja, "Ese correo no parece un correo.", true);
      }

      enviando(forma, true);
      avisar(caja, "");

      llamar("suscribir", {
        correo: datos.correo,
        origen: location.pathname,
        web: datos.web,
        segundos: segundos()
      })
        .then(function (d) {
          forma.reset();
          avisar(caja, d.mensaje || "Te hemos mandado un correo. Pincha el enlace y ya estás dentro.");
        })
        .catch(function (err) {
          avisar(caja, loQueDecir(err,
            "No se ha podido apuntar. Puede ser tu conexión. Inténtalo en un rato."), true);
        })
        .then(function () { enviando(forma, false); });
    });
  }
})();
