-- Los comentarios de Cinco Hache.
--
-- Se pega entero en Supabase: panel del proyecto → SQL Editor → Run.
-- Se puede volver a ejecutar las veces que haga falta sin romper nada.
--
-- La idea de fondo: **el navegador del lector no escribe nunca en esta
-- tabla**. Solo lee, y solo lo que ya está aprobado para verse. Todo lo que
-- entra pasa antes por la función `comentar`, que valida, frena a los robots
-- y avisa por correo. Así la clave que va en el blog —que es pública, la ve
-- cualquiera con el botón derecho— no sirve para nada más que para leer.

-- ── La tabla ─────────────────────────────────────────────────────────────

create table if not exists public.comentarios (
  id         uuid         primary key default gen_random_uuid(),

  -- A qué entrada pertenece. Es el nombre del archivo sin fecha ni
  -- extensión, el mismo que la herramienta pone en el front matter.
  slug       text         not null,

  -- Como quiere que se le llame. Lo único obligatorio además del texto.
  apodo      text         not null,

  -- Su Instagram, sin la arroba. Opcional: mucha gente no querrá darlo,
  -- y obligar a identificarse es justo lo contrario de lo que se busca.
  instagram  text,

  texto      text         not null,
  creado     timestamptz  not null default now(),

  -- Se publica al momento. Esta columna existe para poder esconder algo
  -- desde el correo de aviso sin borrarlo del todo.
  visible    boolean      not null default true,

  -- Huella de quien escribe, para frenar al que manda cien seguidos. Es un
  -- hash con sal: no se guarda ninguna IP, ni se puede sacar de aquí.
  huella     text,

  -- Límites en la propia base de datos, no solo en el formulario. Un
  -- formulario se salta con dos líneas de consola; esto no.
  constraint apodo_con_medida     check (char_length(trim(apodo))     between 1 and 40),
  constraint texto_con_medida     check (char_length(trim(texto))     between 2 and 2000),
  constraint instagram_plausible  check (
    instagram is null
    or instagram ~ '^[A-Za-z0-9._]{1,30}$'
  ),
  constraint slug_plausible       check (slug ~ '^[a-z0-9-]{1,120}$')
);

create index if not exists comentarios_por_entrada
  on public.comentarios (slug, creado desc)
  where visible;

create index if not exists comentarios_por_huella
  on public.comentarios (huella, creado desc);


-- ── Quién puede ver qué ──────────────────────────────────────────────────
--
-- La tabla queda cerrada a cal y canto: se enciende RLS y no se escribe
-- ninguna política para el público. Sin política, no hay acceso. Ni leer,
-- ni escribir, ni contar filas.

alter table public.comentarios enable row level security;

revoke all on public.comentarios from anon, authenticated;


-- ── Lo que sí se puede leer ──────────────────────────────────────────────
--
-- Una vista con las columnas que son de ver y nada más. Fuera `huella`,
-- que es de quien escribe, y fuera `visible`, que es cosa nuestra.
--
-- `security_invoker = false` hace que la vista consulte con los permisos de
-- quien la creó, que es como salta el cierre de arriba de forma controlada:
-- el público entra por esta puerta o no entra.

create or replace view public.comentarios_publicos
with (security_invoker = false) as
  select id, slug, apodo, instagram, texto, creado
  from public.comentarios
  where visible
  order by creado;

grant select on public.comentarios_publicos to anon, authenticated;


-- ── Cuántos hay, sin traerlos todos ──────────────────────────────────────
-- Para poder poner «3 comentarios» en el listado sin descargar el texto.

create or replace function public.contar_comentarios(slugs text[])
returns table (slug text, cuantos bigint)
language sql
stable
security definer
set search_path = public
as $$
  select c.slug, count(*)
  from public.comentarios c
  where c.visible and c.slug = any(slugs)
  group by c.slug;
$$;

grant execute on function public.contar_comentarios(text[]) to anon, authenticated;


-- ── Comprobación ─────────────────────────────────────────────────────────
-- Al ejecutar todo esto debería salir una fila diciendo que está listo.

select
  'listo' as estado,
  (select count(*) from public.comentarios)          as comentarios,
  (select count(*) from pg_policies
    where schemaname = 'public' and tablename = 'comentarios') as politicas_publicas;


-- ═════════════════════════════════════════════════════════════════════════
--  LA NEWSLETTER
-- ═════════════════════════════════════════════════════════════════════════
--
-- Aquí la diferencia con los comentarios es total: los comentarios son
-- públicos por definición y esto es lo contrario. La lista de correos no la
-- puede leer nadie desde el navegador, ni entera ni de una en una, ni
-- siquiera para saber cuántos hay. Se entra solo desde el panel de Supabase
-- o con la llave de servicio, que nunca sale de las funciones.

create table if not exists public.suscriptores (
  id          uuid         primary key default gen_random_uuid(),
  correo      text         not null unique,

  -- 'pendiente' hasta que pincha el enlace del correo de confirmación.
  -- Mandar a quien no lo ha confirmado es lo que hunde la reputación de un
  -- remitente y, en España, lo que da problemas con el RGPD.
  estado      text         not null default 'pendiente'
                           check (estado in ('pendiente', 'confirmado', 'baja')),

  -- Sirve para confirmar y para darse de baja, y no caduca: el enlace de
  -- baja tiene que funcionar siempre, en el correo más viejo que quede.
  ficha       text         not null,

  creado      timestamptz  not null default now(),
  confirmado  timestamptz,
  baja_en     timestamptz,

  -- De qué página se suscribió. Útil para saber qué artículo trae gente.
  origen      text,
  huella      text,

  constraint correo_plausible check (
    correo = lower(correo)
    and correo ~ '^[^@[:space:]]+@[^@[:space:]]+\.[a-z]{2,}$'
    and char_length(correo) <= 254
  )
);

create index if not exists suscriptores_confirmados
  on public.suscriptores (creado desc) where estado = 'confirmado';

create index if not exists suscriptores_por_ficha
  on public.suscriptores (ficha);

alter table public.suscriptores enable row level security;

-- Ni una política. Nadie entra desde fuera, ni para leer ni para contar.
revoke all on public.suscriptores from anon, authenticated;


-- ── La lista para el día que toque enviar ────────────────────────────────
-- Desde el panel de Supabase:  select * from envio;  → Download CSV.
-- Ese CSV se sube a cualquier servicio de envío cuando haga falta.

create or replace view public.envio as
  select correo, creado, confirmado, origen
  from public.suscriptores
  where estado = 'confirmado'
  order by creado;

revoke all on public.envio from anon, authenticated;
