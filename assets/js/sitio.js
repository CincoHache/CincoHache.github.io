/* Cinco Hache — lo poco que hace JavaScript en este sitio.
 *
 *   1. El interruptor de tema, que recuerda tu elección.
 *   2. El buscador y los filtros del archivo.
 *   3. Marcar en el sumario por dónde vas leyendo.
 *   4. El botón de compartir.
 *
 * Nada de esto es imprescindible: sin JavaScript el sitio se lee entero,
 * el archivo sale completo y las fuentes se abren igual, porque son un
 * <details> y de eso se encarga el navegador.
 */

(function () {
  "use strict";

  var raiz = document.documentElement;

  // ── 1 · Tema ──────────────────────────────────────────────────────

  function temaActual() {
    return raiz.getAttribute("data-tema") === "claro" ? "claro" : "oscuro";
  }

  function ponerTema(t) {
    raiz.setAttribute("data-tema", t);
    try { localStorage.setItem("ch-tema", t); } catch (e) { /* privado */ }
    var boton = document.getElementById("cambiar-tema");
    if (boton) {
      boton.setAttribute(
        "aria-label",
        t === "claro" ? "Cambiar a modo oscuro" : "Cambiar a modo claro"
      );
    }
  }

  var botonTema = document.getElementById("cambiar-tema");
  if (botonTema) {
    ponerTema(temaActual());
    botonTema.addEventListener("click", function () {
      ponerTema(temaActual() === "claro" ? "oscuro" : "claro");
    });
  }

  // ── 2 · Buscador y filtros del archivo ────────────────────────────

  var campo = document.getElementById("buscar");
  var filas = [].slice.call(document.querySelectorAll("[data-entrada]"));

  if (campo && filas.length) {
    var botonesFiltro = [].slice.call(document.querySelectorAll("[data-filtro]"));
    var cuenta = document.getElementById("cuenta-resultados");
    var vacio = document.getElementById("sin-resultados");
    var limpiar = document.getElementById("limpiar-busqueda");
    var aviso = document.getElementById("aviso-filtro");
    var avisoTexto = document.getElementById("aviso-filtro-texto");
    var seccionActiva = "";

    function normalizar(s) {
      // Sin tildes: buscar «reseña» debe encontrar «resena» y al revés.
      return (s || "")
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");
    }

    function filtrar() {
      var consulta = normalizar(campo.value.trim());
      var visibles = 0;

      filas.forEach(function (fila) {
        var texto = normalizar(fila.getAttribute("data-busqueda"));
        var seccion = fila.getAttribute("data-seccion");
        var coincide = !consulta || texto.indexOf(consulta) !== -1;
        var deLaSeccion = !seccionActiva || seccion === seccionActiva;
        var mostrar = coincide && deLaSeccion;
        fila.hidden = !mostrar;
        if (mostrar) visibles++;
      });

      if (cuenta) {
        cuenta.textContent =
          visibles + (visibles === 1 ? " resultado" : " resultados");
      }
      if (vacio) vacio.hidden = visibles !== 0;
      if (limpiar) limpiar.hidden = campo.value === "";

      var hayFiltro = Boolean(consulta) || Boolean(seccionActiva);
      if (aviso) aviso.hidden = !hayFiltro;
      if (avisoTexto) {
        var partes = [];
        if (seccionActiva) {
          var b = botonesFiltro.filter(function (x) {
            return x.getAttribute("data-filtro") === seccionActiva;
          })[0];
          if (b) partes.push(b.textContent.trim());
        }
        if (consulta) partes.push("«" + campo.value.trim() + "»");
        avisoTexto.textContent = partes.join(" · ");
      }
    }

    campo.addEventListener("input", filtrar);

    botonesFiltro.forEach(function (boton) {
      boton.addEventListener("click", function () {
        var valor = boton.getAttribute("data-filtro");
        seccionActiva = seccionActiva === valor ? "" : valor;
        botonesFiltro.forEach(function (b) {
          b.setAttribute(
            "aria-pressed",
            String(b.getAttribute("data-filtro") === seccionActiva)
          );
        });
        filtrar();
      });
    });

    if (limpiar) {
      limpiar.addEventListener("click", function () {
        campo.value = "";
        filtrar();
        campo.focus();
      });
    }

    var quitar = document.getElementById("quitar-filtros");
    if (quitar) {
      quitar.addEventListener("click", function () {
        campo.value = "";
        seccionActiva = "";
        botonesFiltro.forEach(function (b) {
          b.setAttribute("aria-pressed", "false");
        });
        filtrar();
      });
    }

    // Una etiqueta del artículo llega como /trabajos/?q=ciudad
    var parametros = new URLSearchParams(window.location.search);
    if (parametros.get("q")) {
      campo.value = parametros.get("q");
    }
    if (parametros.get("seccion")) {
      seccionActiva = parametros.get("seccion");
      botonesFiltro.forEach(function (b) {
        b.setAttribute(
          "aria-pressed",
          String(b.getAttribute("data-filtro") === seccionActiva)
        );
      });
    }
    filtrar();

    // La lupa de la cabecera trae a #buscar: al llegar, el cursor dentro.
    if (window.location.hash === "#buscar") campo.focus();
  }

  // ── 3 · Sumario: marcar el ladillo en pantalla ────────────────────

  var enlacesSumario = [].slice.call(document.querySelectorAll("[data-sumario]"));
  if (enlacesSumario.length && "IntersectionObserver" in window) {
    var ladillos = enlacesSumario
      .map(function (a) { return document.getElementById(a.getAttribute("data-sumario")); })
      .filter(Boolean);

    var observador = new IntersectionObserver(
      function (entradas) {
        entradas.forEach(function (entrada) {
          if (!entrada.isIntersecting) return;
          enlacesSumario.forEach(function (a) {
            a.classList.toggle(
              "sumario__enlace--activo",
              a.getAttribute("data-sumario") === entrada.target.id
            );
          });
        });
      },
      { rootMargin: "-80px 0px -70% 0px", threshold: 0 }
    );

    ladillos.forEach(function (h) { observador.observe(h); });
  }

  // ── 4 · Compartir ─────────────────────────────────────────────────

  var compartir = document.getElementById("compartir");
  if (compartir) {
    compartir.addEventListener("click", function () {
      var datos = {
        title: compartir.getAttribute("data-titulo") || document.title,
        url: window.location.href
      };
      if (navigator.share) {
        navigator.share(datos).catch(function () { /* cancelado */ });
        return;
      }
      if (navigator.clipboard) {
        navigator.clipboard.writeText(datos.url).then(function () {
          var antes = compartir.textContent;
          compartir.textContent = "Enlace copiado";
          setTimeout(function () { compartir.textContent = antes; }, 1800);
        });
      }
    });
  }
  /* ── Los favoritos ────────────────────────────────────────────────────
   *
   * Filtra y busca sobre fichas que Jekyll ya ha pintado. Sin JavaScript la
   * página se lee entera, ordenada por fecha; lo único que se pierde son
   * los botones. Por eso no hay nada aquí que construya contenido.
   */

  var campoFav = document.querySelector("[data-buscar-favoritos]");
  var fichas = [].slice.call(document.querySelectorAll("[data-lista-favoritos] .ficha"));

  if (campoFav && fichas.length) {
    var botonesMedio = [].slice.call(document.querySelectorAll("[data-medio][aria-pressed]"));
    var vacioFav = document.getElementById("favoritos-sin-resultados");
    var avisoFav = document.getElementById("aviso-favoritos");
    var avisoFavTexto = document.getElementById("aviso-favoritos-texto");
    var quitarFav = document.getElementById("quitar-favoritos");
    var medioActivo = "";

    function limpiarTexto(s) {
      return (s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    }

    function filtrarFavoritos() {
      var consulta = limpiarTexto(campoFav.value.trim());
      var visibles = 0;

      fichas.forEach(function (ficha) {
        var texto = limpiarTexto(ficha.getAttribute("data-busca"));
        var delMedio = !medioActivo || ficha.getAttribute("data-medio") === medioActivo;
        var casa = !consulta || texto.indexOf(consulta) !== -1;
        var mostrar = casa && delMedio;
        ficha.hidden = !mostrar;
        if (mostrar) visibles++;
      });

      if (vacioFav) vacioFav.hidden = visibles !== 0;

      var hayFiltro = consulta || medioActivo;
      if (avisoFav) {
        avisoFav.hidden = !hayFiltro;
        if (hayFiltro && avisoFavTexto) {
          avisoFavTexto.textContent =
            visibles + (visibles === 1 ? " ficha" : " fichas");
        }
      }
    }

    campoFav.addEventListener("input", filtrarFavoritos);

    botonesMedio.forEach(function (boton) {
      boton.addEventListener("click", function () {
        var id = boton.getAttribute("data-medio");
        medioActivo = medioActivo === id ? "" : id;
        botonesMedio.forEach(function (b) {
          b.setAttribute("aria-pressed", b.getAttribute("data-medio") === medioActivo);
        });
        filtrarFavoritos();
      });
    });

    if (quitarFav) {
      quitarFav.addEventListener("click", function () {
        campoFav.value = "";
        medioActivo = "";
        botonesMedio.forEach(function (b) { b.setAttribute("aria-pressed", "false"); });
        filtrarFavoritos();
        campoFav.focus();
      });
    }

    /* Entrar desde otra página con el filtro puesto: /favoritos/#libro */
    var ancla = (location.hash || "").replace("#", "");
    if (ancla) {
      var elegido = botonesMedio.filter(function (b) {
        return b.getAttribute("data-medio") === ancla;
      })[0];
      if (elegido) elegido.click();
    }
  }
})();
