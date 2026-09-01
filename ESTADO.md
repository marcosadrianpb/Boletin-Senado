# Boletín diario de proyectos del Senado — Estado del proyecto

Última actualización: 31 de agosto de 2026 · **Fase 2 cerrada: once días en producción.
El envío por mail sigue apagado, falta configurarlo en Brevo y en GitHub.**
**Los pasos para retomar están en [Próximo paso](#próximo-paso).**

## Objetivo

Detectar todos los días qué proyectos nuevos ingresaron al Senado de la Nación,
armar un boletín con ese listado y enviarlo por mail a una lista de difusión chica
(menos de 50 destinatarios).

## Decisiones tomadas

| Tema | Decisión |
|---|---|
| Alcance | Todo lo que ingresa, sin filtro de tipo ni temático |
| Fuente | `POST /parlamentario/parlamentaria/avanzada` filtrando por **año de expediente**, más su exportación XLS |
| Por qué por año y no por fecha | El Senado carga expedientes con fecha retroactiva. El año del expediente no cambia nunca |
| Detección de novedades | Padrón completo del año, comparado por **conjunto de claves** contra la corrida anterior |
| Clave de un expediente | `(número, origen)` — el número solo se repite entre orígenes |
| Contenido del mail | Listado crudo: expediente, tipo, fecha, autores, comisiones, extracto y link. Sin resúmenes generados |
| Entrega inicial | Un issue de GitHub por día; el envío del mail arranca manual |
| Proveedor de mail | Brevo, plan gratis (300/día). Sin dominio propio: todo tiene que salir cero pesos hasta que haga falta otra cosa |
| Remitente | `proparlamentariasenado@gmail.com`, con el nombre visible **Boletin proyectos ingresados** |
| Infraestructura | GitHub Actions, repo público `marcosadrianpb/Boletin-Senado` |
| Lenguaje | Python 3.11 + `requests` + `xlrd` + `beautifulsoup4`. **Sin Playwright** |
| Horario | 8:00 de Buenos Aires, días hábiles (`cron: 0 11 * * 1-5`) |

Los días sin novedades no abren issue: la corrida igual corre, actualiza el padrón y deja
la cuenta en el historial. Si conviene lo contrario, se cambia una condición del workflow.

## Fases

- **Fase 0 — Reconocimiento.** ✅ CERRADA.
- **Fase 1 — Extractor y padrón.** ✅ CERRADA. Corrida 0 y primera comparación, las dos
  verificadas en Actions.
- **Fase 2 — Boletín e issue diario.** ✅ CERRADA. Once días en producción, siete issues.
- **Fase 3 — Envío por mail.** ← acá estamos. El código está escrito y subido, y el paso
  del workflow está apagado hasta que existan el secret y la variable.
- **Fase 4 — Endurecimiento.**

## Cómo funciona la extracción

Tres pedidos HTTP planos, sin navegador:

1. `GET /parlamentario/parlamentaria/` → sale el token CSRF `busqueda_proyectos[_token]`
2. `POST /parlamentario/parlamentaria/avanzada` con `busqueda_proyectos[expedienteNumeroPos] = 2026`
   y el resto de los campos del formulario vacíos
3. `GET /micrositios/DatosAbiertosExpedientes/BusquedaAvanzada/XLS` → el resultado entero

Medido el 19/8/2026: **2014 expedientes de 2026, 900 KB, un segundo**. Verificado contra el
listado paginado (202 páginas, la última con 3 filas): el XLS no viene truncado.

Columnas del XLS: `Numero Expediente | Tipo | Origen | Extracto`. No trae fecha ni autor.

Dos asteriscos:

- El XLS tiene la estructura OLE mal cerrada. `xlrd` lo abre solo con
  `ignore_workbook_corruption=True`.
- Cloudflare no bloquea: probado con User-Agent propio y con `python-requests`, ambos 200.

### La clave es (número, origen)

De 2014 filas hay solo ~1361 números distintos: la numeración arranca de cero por cada
origen. `1/26` existe a la vez para CD, OV y PE. Con `(número, origen)` no hay un solo
duplicado. Si la comparación usara el número solo, se perderían proyectos.

### Ficha por expediente

La avanzada no trae link por fila, pero la ruta se arma con los datos que ya tenemos:

```
/parlamentario/comisiones/verExp/{numero}.{año}/{origen}/{tipo}
```

`1361/26` + `S` + `PD` → `/verExp/1361.26/S/PD`. Probado con S/PD, S/PL, S/CC, OV/CM,
PE/DC y P/PP: los seis dan 200.

Esa página trae lo que falta: fecha de mesa de entradas, **autores con nombre y apellido
completo** (`Vischi , Eduardo Alejandro`, en vez de deducir "VISCHI" del extracto), giros a
comisiones con orden y fecha, número de DAE, y link al PDF del texto original
(`/parlamentario/parlamentaria/{id}/downloadPdf`).

Se le pega **solo a los expedientes nuevos del día** — diez o treinta, no los dos mil del
padrón. Las tablas se identifican por su atributo `summary`, que es estable.

## Cómo funciona la comparación

- La **corrida 0** carga el padrón completo y no anuncia nada: no hay contra qué comparar.
  Queda como punto de partida.
- Cada corrida siguiente vuelve a bajar el padrón entero, saca la diferencia y lo actualiza.
- Se compara el **conjunto de claves**, no la cantidad total. Si un día entran dos y se
  retira uno, el total sube en uno solo y contar no alcanza para saber cuáles son. El total
  igual se guarda en `datos/historial.jsonl`, una línea por corrida.
- Las bajas no se borran del padrón: quedan con `vigente: false`. Si el expediente vuelve a
  aparecer se anuncia como **reingreso**, no como alta nueva.
- Si cambia el extracto o el tipo de un expediente ya conocido, sale como **corrección**.
- **Cambio de año:** en enero y febrero se consultan el año en curso y el anterior. La
  primera vez que se consulta un año nuevo, sus expedientes entran al padrón como línea de
  base de ese año (`absorbidos`) y no se anuncian, así el boletín de enero no sale con dos
  mil entradas. De los absorbidos se guarda solo la cuenta: el detalle ya está en el padrón.
- Si la descarga trae menos de la mitad del padrón vigente, la corrida aborta sin tocar
  nada: es más probable una falla de la fuente que una purga real.
- **Un día puede tener más de una corrida** —la del cron y alguna a mano— y las novedades
  del día son la **unión** de lo que encontró cada una. La segunda corrida compara contra un
  padrón que la primera ya actualizó, así que por sí sola no ve nada. Por eso el archivo del
  día se acumula en vez de reescribirse (`padron.acumular`), y lleva la cuenta de `corridas`.
  Un expediente no puede estar en dos listas del mismo día: si entró hoy y después le
  corrigieron el texto es una sola novedad, con el texto corregido; y una baja de la mañana
  queda sin efecto si a la tarde el expediente volvió a aparecer.

## Cómo se arma el boletín

`src/boletin.py` lee `datos/novedades/YYYY-MM-DD.json` y escribe el texto. No toca la red ni
el padrón: todo lo que necesita ya está en ese archivo, que es lo que dejó la corrida. Por
eso el mismo cuerpo va a servir después para el mail de la Fase 3, sin volver a consultar
nada.

- **Agrupado por tipo**, en un orden fijo: primero lo que se legisla (leyes, declaraciones,
  comunicaciones, resoluciones), después acuerdos y decretos, y al final las comunicaciones
  varias. Si no fuera así, los proyectos de ley quedarían enterrados entre los informes de
  la AGN, que son un tercio del padrón.
- Cada expediente entra con su número enlazado a la ficha, el origen, la fecha de mesa de
  entradas, el DAE, el extracto crudo, los autores con nombre completo, los giros a
  comisiones y el link al PDF del texto. Nada de esto se resume ni se reescribe.
- Los códigos de tipo y de origen se muestran con el nombre que les da el propio formulario
  del Senado (`PL` → proyecto de ley, `OV` → oficiales varios). Si aparece un código que no
  está en la tabla, se muestra el código y el boletín sale igual.
- Los expedientes se ordenan por número, no alfabéticamente: `51/26` antes que `276/26`.
- Correcciones y bajas van al final, en una línea cada una. La corrección muestra el texto
  viejo y el nuevo.
- Si un expediente no tiene ficha —porque el día trajo más de 80 altas y no se enriquecen,
  o porque la consulta falló— igual sale, con el link armado a mano y el extracto.
- **Días sin novedades: no hay boletín ni issue.** El script termina bien, avisa por qué y
  deja `hay=false` para que el workflow saltee el paso del issue.
- El cuerpo del issue de GitHub no puede pasar los 65.536 caracteres. Si el boletín no
  entra, se corta antes del último expediente que entra y avisa dónde está el archivo
  completo. El `.md` que se commitea nunca se recorta.

El issue lo abre el mismo workflow con `gh issue create`, con la etiqueta `boletin` y el
título `Boletín del Senado - 2026-08-20 - 8 nuevos, 1 corrección, 1 baja`.

## Estado del repo

Todo subido. Últimos commits:

```
7a6b7d4  Fase 3: envio por Brevo, apagado hasta que se configure
b638530  Fase 3: el mail en HTML y la decision del remitente
f915932  Fase 2: boletin diario e issue automatico
6f239a9  Padron del 2026-08-20          <- lo commiteo el workflow
1bd58af  Fase 1: extraccion por anio de expediente y padron comparable
```

- `src/senado.py` — cliente del buscador. Baja y parsea. No guarda estado.
- `src/padron.py` — el padrón y la comparación. No toca la red.
- `src/actualizar.py` — la corrida diaria: baja, compara, actualiza, escribe novedades.
- `src/boletin.py` — arma el texto del boletín. No toca la red ni el padrón.
- `src/senadores.py` — quién es cada senador y en qué bloque está. No lo usa el padrón.
- `src/resumen.py` — las cuentas del día: total, por tipo, por bloque, por comisión.
- `src/correo.py` — el mismo boletín en HTML de correo, más su versión en texto.
- `src/envio.py` — crea la campaña en Brevo y, si se le pide, la manda.
- `.github/workflows/actualizar.yml` — la corrida diaria, y a mano.
- `.github/workflows/probar-mail.yml` — banco de pruebas del envío: arma la campaña
  con un día ya archivado, sin tocar el padrón ni el repo.
- `requirements.txt`
- `.github/workflows/recon.yml`, `INFORME.md`, `recon/` — Fase 0, ya cumplieron su función.
  `INFORME.md` está duplicado (raíz y `recon/`); conviene dejar uno solo.

En `_to_delete/`, fuera del repo por el `.gitignore`, quedaron `extractor_playwright.py` y
`extraer_playwright.yml`: la versión vieja de Fase 1 basada en Playwright y en `fechaMesa`.
Nunca se subió.

### Archivos que genera

```
datos/padron.json                  el padron completo, clave -> expediente
datos/novedades/YYYY-MM-DD.json    altas, bajas, reingresos y correcciones del dia
datos/historial.jsonl              una linea por corrida: total, altas, bajas
datos/boletines/YYYY-MM-DD.md      el boletin del dia, solo si hubo novedades
datos/senadores.json               id -> nombre y bloque, se refresca semanal
```

Formato de cada expediente en el padrón:

```json
{
  "expediente": "1361/26",
  "tipo": "PD",
  "origen": "S",
  "extracto": "VISCHI: PROYECTO DE DECLARACIÓN QUE ...",
  "anio": 2026,
  "vigente": true,
  "visto": "2026-08-19"
}
```

Y la ficha que se le agrega a los nuevos del día:

```json
{
  "url": "https://www.senado.gob.ar/parlamentario/comisiones/verExp/1361.26/S/PD",
  "fecha_mesa": "2026-08-12",
  "dae": "59/2026",
  "dae_tipo": "NORMAL",
  "autores": ["Vischi , Eduardo Alejandro"],
  "comisiones": [{"comision": "DE RELACIONES EXTERIORES Y CULTO", "orden": "1", "ingreso": "14-08-2026"}],
  "texto_pdf": "https://www.senado.gob.ar/parlamentario/parlamentaria/498623/downloadPdf"
}
```

## La corrida 0

Corrida el 19/8/2026 a mano desde Actions. Resultado: **2014 expedientes** cargados como
punto de partida, sin anunciar novedades.

El padrón commiteado se bajó del repo y se verificó:

```
expedientes : 2014          vigentes : 2014
claves mal formadas : 0     claves incoherentes : 0
sin extracto : 0            sin tipo : 0      sin origen : 0
anio != 2026 : 0            visto : 2026-08-19 (los 2014)
```

Y se comparó contra la extracción hecha en la máquina del usuario, desde Argentina, minutos
antes: **mismo conjunto de claves, cero extractos distintos**. El runner de GitHub, con IP
de Estados Unidos, trae exactamente lo mismo. Queda descartado que la fuente sirva contenido
distinto según de dónde le peguen.

Primera línea del historial:

```json
{"fecha":"2026-08-19","total":2014,"altas":0,"bajas":0,"linea_base":true}
```

### Composición del padrón al 19/8/2026

Como el alcance es "todo lo que ingresa", cerca de un tercio son comunicaciones y acuerdos,
no proyectos.

| Origen | | Tipo | |
|---|---|---|---|
| S — Senado | 1360 | PL Proyecto de ley | 572 |
| OV — Oficiales varios | 353 | PD Proyecto de declaración | 431 |
| PE — Poder Ejecutivo | 275 | CV Comunicaciones varias | 246 |
| P — Particulares | 20 | AC Acuerdos | 211 |
| CD — Diputados | 6 | CC Comunicaciones de comisiones | 151 |
| | | PC Proyecto de comunicación | 138 |
| | | resto (CA, CO, PP, DC, CE, PR, MD, CM, MS) | 265 |

Por eso el boletín conviene agruparlo por tipo, para que los proyectos de ley no queden
enterrados entre comunicaciones de la AGN. Es decisión de presentación: la extracción trae
todo igual.

## Pruebas hechas (19/8/2026, contra el sitio real)

En la máquina del usuario, antes de subir:

- Corrida 0: 2014 expedientes cargados.
- Corrida repetida sin cambios: 0 altas, 0 bajas. Es idempotente.
- Día simulado sacando 5 expedientes del padrón, ensuciando el extracto de uno y dando de
  baja otro: detectó 5 altas, 1 corrección y 1 reingreso, y trajo las 6 fichas con autores,
  comisiones y PDF.

En Actions:

- Corrida 0 real, verificada contra la extracción local (ver arriba).

## La primera corrida automática (20/8/2026)

Salió sola a las 8:00 AR, la primera que compara en vez de cargar:

```json
{"fecha":"2026-08-20","total":2014,"altas":0,"bajas":0,"linea_base":false}
```

El Senado no cargó nada entre el 19 y el 20. Sirvió igual: es la primera vez que el camino
de comparación corre en Actions y no solo en local, y dio lo que tenía que dar.

## Pruebas del boletín (20/8/2026, contra el sitio real)

Con el padrón de verdad, en una copia fuera del repo:

- Le saqué 8 expedientes de tipos distintos, le ensucié el extracto a uno e inventé uno que
  hoy no existe. La corrida detectó **8 altas, 1 corrección y 1 baja**, trajo las 8 fichas
  y el boletín salió agrupado por tipo, con autores, comisiones y PDF.
- Otra pasada con 5 expedientes sacados, para ver el resumen del run y las salidas que
  consume el workflow (`hay`, `titulo`, `archivo`, `cuerpo`).
- Casos raros: expediente sin ficha, tipo desconocido (`ZZ`) y ficha que falló. Los tres
  salen en el boletín sin romperlo.
- Recorte a 2.500 caracteres para forzar el tope del issue: corta antes de un expediente,
  no deja títulos de sección colgando y avisa dónde está el completo.
- Días sin novedades (19 y 20 de agosto): no arma boletín, deja `hay=false`.

Lo único que falta ver es el `gh issue create` en Actions: hasta que no haya un día con
altas, el paso se saltea solo.

## Once días en producción (20 al 31 de agosto)

El sistema corrió solo, sin tocarlo. Resultado:

| | |
|---|---|
| Issues abiertos | 7 |
| Boletines commiteados | 6 |
| Expedientes nuevos detectados | 63 (padrón 2014 → 2077) |
| Fichas que fallaron | 0 |

**En once días no entró ni un proyecto de ley ni una declaración.** Los PL siguen en 572 y
los PD en 431, los mismos números que el 19 de agosto. Está verificado contra el padrón: no
se pierde nada, el Senado no cargó proyectos nuevos en esa ventana. Lo que entró son
acuerdos del Ejecutivo para designar jueces, comunicaciones de la AGN y peticiones de
particulares.

### Los dos defectos que aparecieron, y su arreglo

**1. Los días con dos corridas perdían la mitad del día.** El 26/8 se abrieron *dos* issues,
el #4 con las 7 correcciones de la mañana y el #5 con las 5 altas de la tarde, cada uno con
un pedazo. Y `datos/novedades/2026-08-25.json` quedó diciendo `altas 0` cuando ese día
entraron 29: la corrida de las 8:16 pisó la de las 3:38. El boletín en markdown se salvó de
casualidad, porque no se reescribe cuando no hay novedades.

Esto además bloqueaba el mail, que lee ese mismo archivo: un día con dos corridas se habría
mandado vacío. Arreglado en dos partes: el archivo del día acumula (ver *Cómo funciona la
comparación*), y el issue del día se actualiza en vez de abrirse de nuevo. El workflow lo
busca por etiqueta y no con `--search`, porque la búsqueda de GitHub tarda en indexar y un
issue recién creado no aparece. `envio.py` hace lo mismo con la campaña: si ya existe y
sigue en borrador, le pone el día completo; si ya se mandó, no manda otra.

**2. El cron llegaba tarde, y no un poco.** Las corridas programadas de la última semana
salieron 17:44, 21:16 y 20:50 UTC: 14:44, 18:16 y 17:50 de Buenos Aires, en vez de las 8:00.
GitHub demora los workflows programados cuando tiene carga y la hora en punto es el peor
momento. El cron pasó de `0 11` a **`23 10`**: minuto no redondo y 37 minutos de adelanto
como margen. No hay garantía —GitHub no la da para workflows programados—, así que hay que
medirlo una semana. Si sigue llegando tarde, la salida es dispararlo desde afuera.

## Próximo paso

Todo el código está subido y funcionando. El envío por mail está **apagado**: el paso del
workflow no hace nada hasta que existan la variable y el secret. Lo que falta son cinco
cosas, en este orden, y las cuatro primeras son de cuenta y credenciales.

**1. Las dos listas de contactos, en Brevo → Contacts → Lists.**
Una `Prueba`, con la casilla propia de Gmail más una de Outlook y una de Yahoo: los tres
filtran distinto y es la única forma de medir sin mandarle a nadie de verdad. Otra
`Boletin Senado`, vacía por ahora. El id de cada lista se ve en la URL al abrirla.

**2. La API key, en Brevo → SMTP & API → API keys → Generate a new API key.**
Copiarla en el momento: después no la vuelve a mostrar.

**3. El secret, en el repo → Settings → Secrets and variables → Actions → pestaña Secrets.**
`New repository secret`, nombre `BREVO_API_KEY`, valor la clave.

**4. La variable, en la misma pantalla, pestaña Variables.**
`New repository variable`, nombre `BREVO_LISTA`, valor el id de la lista **de prueba**.
`BREVO_ENVIAR` todavía no: sin ella la campaña se crea y queda en borrador.

**5. Esperar el primer día con altas.** El workflow va a armar la campaña y dejarla sin
mandar. Hay que abrirla en Brevo y mirar la previsualización. Ojo que en esta ventana hubo
varios días seguidos sin novedades: puede tardar en llegar.

Si no se quiere esperar al Senado, se puede agregar al workflow un disparo manual que arme
la campaña con un día simulado. No está hecho; es media hora.

### Y después, la verificación

1. Poner `BREVO_ENVIAR` en `true`. La corrida siguiente manda a la lista de prueba.
2. En el mail que llegue a Gmail: menú del mensaje → **Mostrar original**. Ahí está el `From`
   real —que responde la pregunta del `brevosend.com`— y el `Authentication-Results`, que
   tiene que decir `spf=pass` y `dkim=pass`.
3. Pasar el mismo mail por mail-tester y anotar el puntaje.
4. Confirmar que en Outlook y en Yahoo entró a la bandeja y no a spam.
5. Recién con eso, cambiar `BREVO_LISTA` por el id de la lista real.

Si cae en spam, las salidas son las dos que ya se discutieron y no hay una tercera gratis:
dominio propio, o mandar por el SMTP de Gmail con la lista guardada en un secret. Medir
primero.

### Y medir el horario

Con el cron en `23 10`, anotar una semana a qué hora salieron las corridas programadas. Se
ve en la lista de Actions o pidiendo `/actions/runs` a la API. Si la demora sigue siendo de
horas, hay que dispararlo desde afuera en vez de con el cron de GitHub.

## Arreglado después de la corrida 0

- `upload-artifact` de v4 a v7: el runner avisa que Node 20 está deprecado.
- El archivo de novedades de la línea de base guardaba los 2014 expedientes absorbidos, que
  son los mismos que están en `padron.json`. Ahora guarda solo la cuenta: **de 591 KB a 289
  bytes**. El archivo gordo ya se reemplazó por el chico.
- El resumen del run que escribía `actualizar.py` tenía una tabla con las altas; ahora la
  presentación es toda del boletín y `actualizar.py` deja solo las cuentas de la corrida.

## Cómo se manda el mail

`src/correo.py` arma el cuerpo a partir del mismo archivo de novedades que el issue, así que
el listado es idéntico y no se pueden desincronizar. Es HTML de correo, no de web: tablas en
vez de flex, estilos escritos en cada etiqueta, sin javascript ni imágenes. Es lo único que
renderizan igual Gmail, Outlook y el resto. Ancho de 640 px, y si el mail pasa de 90 KB se
corta con un aviso, porque arriba de 102 KB Gmail lo recorta solo y rompe el listado.

`src/envio.py` lo manda con la **API de campañas** de Brevo, no con la de transaccionales.
La de campañas maneja la lista: agrega sola el encabezado `List-Unsubscribe`, reemplaza el
`{{ unsubscribe }}` del pie por el link de baja de cada destinatario y deja las
estadísticas. La contra es que no recibe una versión de texto plano —Brevo la genera del
HTML—, así que `correo.texto_plano` queda para el archivo y para el día que haga falta la
transaccional.

Tres frenos, porque un mail mandado no se puede desmandar:

- Sin `--mandar`, la campaña se crea y **queda en borrador**.
- Sin `--lista`, no manda: no existe el envío a nadie.
- Si ya hay una campaña del día, no crea otra. El workflow puede correr dos veces —ya pasó—
  y eso no puede significar dos mails.

Además está `--seco`, que no toca la red y muestra qué mandaría.

### Cómo se configura

El paso del workflow no hace nada hasta que existan estas tres cosas en el repo:

| Dónde | Nombre | Para qué |
|---|---|---|
| Secret | `BREVO_API_KEY` | La clave de la API. No se escribe nunca en el log |
| Variable | `BREVO_LISTA` | Id de la lista de Brevo; si son varias, separados por espacio |
| Variable | `BREVO_ENVIAR` | Con `true` manda; con cualquier otra cosa deja el borrador |

La idea es arrancar apuntando a una lista de prueba con `BREVO_ENVIAR` sin poner, mirar el
borrador en Brevo, después ponerlo en `true` contra la lista de prueba, medir, y recién ahí
cambiar `BREVO_LISTA` por la lista de verdad.

### El banco de pruebas

`probar-mail.yml` existe para no tener que esperar a que el Senado cargue algo. Se dispara a
mano desde Actions con tres campos: la **fecha** de un boletín ya archivado (por ejemplo
`2026-08-28`, que tuvo 14 altas), la **lista** y un tilde para **mandar**. Sin ese tilde
arma la campaña y la deja en borrador; sin el secret cargado corre en seco y no toca Brevo.
En los dos casos sube el HTML como artifact, así se puede bajar y abrir.

Dos cosas que rechazó Brevo en las primeras vueltas, por si reaparecen:

- La clave que va es la de la pestaña **Claves API**, no la de **SMTP**. La de API empieza
  con `xkeysib-`; la SMTP, con `xsmtpsib-`. Con la equivocada contesta
  `401 {"message":"Key not found"}`.
- **Etiquetar campañas es de los planes pagos.** El gratis contesta `405 method_not_allowed:
  "You are not allowed to avail tag option for your campaign"`. Por eso el campo `tag` no va
  salvo que se lo pidan con `--etiqueta`.

Ojo con una cosa al probar días viejos: las fichas anteriores al 31/8 no guardan el id del
autor, así que en esos días el panel por bloque agrupa todo por origen. Los días nuevos sí
lo traen.

El asunto del mail dice **"Proyectos ingresados 28/08/2026 - 14 expedientes nuevos"**, no
"Boletín del Senado": tiene que decir lo mismo que el remitente y que el encabezado, y no
dar a entender que el mail sale del Senado. El nombre de la campaña adentro de Brevo es
"Proyectos ingresados AAAA-MM-DD", que además es la clave con la que se busca si la del día
ya existe.

Remitente: `proparlamentariasenado@gmail.com`, con el nombre visible
**Boletin proyectos ingresados**. Ese nombre es lo que ve la gente en la bandeja; el que
quiera cambiarlo, que lo haga antes del primer envío: moverlo después le mueve el piso a
los filtros. En el código está en `REMITENTE_NOMBRE`, en `src/envio.py`.

## El tablero del mail

El mail abre con las cuentas del día y el listado va abajo, plegado. La idea es que se
entienda de un vistazo qué entró, sin tener que leer 27 extractos.

- **Recuadros**: el total y los dos tipos más grandes.
- **Un treemap** que cruza qué entró con quién lo presentó (ver abajo).
- **Por comisión**, en renglones con su cantidad.
- Después un corte, "DETALLE DE PROYECTOS", y ahí cada tipo en un bloque plegable con la
  ficha completa de siempre: expediente, origen, fecha, DAE, extracto, autores, giros y PDF.

### El treemap

Cada banda es un tipo de expediente y su alto sale de cuántos entraron; adentro, cada celda
es quién lo presentó y su ancho sale de cuántos presentó. Así el área de cada celda queda
proporcional a su cantidad, que es lo que un treemap tiene que cumplir, y cada rectángulo es
un cruce: tipo × bloque.

Decisiones, y por qué:

- **En bandas por tipo, no con el algoritmo "squarified" clásico.** Ese ordena todo por
  tamaño para que los rectángulos queden cuadrados, y al hacerlo mezcla los tipos. Se probó:
  quedaban un proyecto de ley, un acuerdo y una comunicación en la misma franja. En un cruce
  eso es peor que un rectángulo feo, porque el color deja de agrupar.
- **Alto mínimo de banda y ancho mínimo de celda**, siempre hacia arriba. Sin eso, un tipo
  con un expediente en un día de cuarenta queda de tres píxeles. La cantidad va escrita en
  cada celda, así que el número manda sobre el área.
- El reparto del alto es **proporcional con mínimo**: las bandas que no llegan al mínimo se
  fijan ahí y el resto se reparte entre las demás, repitiendo hasta que cierre. La primera
  versión le descontaba a la banda más grande y daba vuelta las proporciones: el tipo de
  cinco expedientes quedaba más chico que el de tres.
- **Colores**: los slots de la guía de visualización en su orden fijo, sin saltear ninguno,
  porque los pares vecinos de esa secuencia están validados para daltonismo. Cinco tipos
  llevan color y el resto va en gris. **La identidad nunca depende del color**: cada banda
  lleva su nombre escrito, así que la paleta solo refuerza.
- **La tinta de cada celda se calcula** por contraste real contra el fondo, no a ojo. Sobre
  el naranja, el aqua y el gris, el negro contrasta casi el doble que el blanco.

### Lo que no puede entrar en el treemap

**La comisión.** Un expediente se gira a dos o tres a la vez: si se le asigna área, la suma
da más que el total del día y el dibujo miente. Es una relación de muchos a muchos, no una
partición. Va como renglones aparte, con su cuenta.

### Cómo se cuenta

- **Bloque**: el del primer autor, que es quien presenta. Los que no tienen autor —acuerdos
  del Ejecutivo, comunicaciones de oficiales varios, peticiones de particulares— se agrupan
  por su origen y se dibujan en gris, para que el panel diga quién presentó en vez de quedar
  en "sin datos". El cruce es por el **id del senador**, que viene en el link del autor en la
  ficha (`/senadores/senador/561`): es exacto y no depende de cómo esté escrito el apellido.
- **Comisión**: un expediente puede ir a más de una, así que la suma puede dar más que el
  total. Los que no tienen giro se cuentan aparte.
- Todo se calcula sobre las **altas**. Reingresos, correcciones y bajas van abajo.
- Los paneles muestran hasta ocho renglones y el resto lo cuentan: un día grande toca quince
  comisiones distintas.

### Lo que se midió antes de armarlo

Sobre los 34 expedientes que entraron con ficha capturada el mismo día:

| tipo / origen | con comisión ya asignada |
|---|---|
| AC / PE — acuerdos | 15 de 15 |
| CO / S — comunicaciones de senadores | 6 de 6 |
| DC y CE / PE | 2 de 2 |
| PP / P — peticiones de particulares | 0 de 5 |
| CV / OV — comunicaciones varias | 0 de 5 |

O sea: **lo que va a comisión entra ya girado**, y lo que no tiene giro es porque no le
corresponde. El panel por comisión sirve desde el primer día.

### Decisiones de HTML

- Las barras son **dos celdas de tabla**, no una imagen ni un SVG. Outlook bloquea las
  imágenes por defecto, Gmail no renderiza SVG y ningún cliente corre javascript.
- El listado va en `<details>`. Donde el cliente sabe plegar —Apple Mail, iOS— el lector abre
  y cierra; donde no —Gmail, Outlook— se ve abierto y el título queda como encabezado de
  sección. **Nadie se queda sin el listado**, que era el riesgo.
- Los paneles van apilados y no de a dos columnas: en un teléfono dos columnas de barras no
  se leen.
- El encabezado dice "Boletín de proyectos ingresados", no "Senado de la Nación Argentina".
  Si el boletín sale institucionalmente por la Prosecretaría, se cambia esa línea y listo;
  mientras no esté confirmado, no puede parecer una comunicación oficial del Senado.

## El remitente y el spam

La pregunta que ordena todo esto es una sola: **el dominio que figura en el From, ¿es
nuestro o no?** No alcanza con que el mail esté firmado; tiene que estar firmado *por el
dominio del remitente*. Eso se llama alineación y es lo que miran Gmail, Outlook y Yahoo.

- **SPF**: un registro en el DNS del dominio que dice qué servidores pueden mandar en su nombre.
- **DKIM**: la firma criptográfica de cada mail; la clave pública también vive en ese DNS.
- **DMARC**: la política de qué hacer si un mail dice venir del dominio y no lo puede probar.

Los tres viven en el DNS del dominio, así que **solo se pueden configurar si el dominio es
tuyo**. `gmail.com` no lo es, y por eso Brevo marca el remitente como "no conforme".

### Lo que hay en la cuenta de Brevo, al 20/8/2026

La cuenta gratuita está creada y `proparlamentariasenado@gmail.com` figura **verificado**,
con dos advertencias que son exactamente este problema:

- **Firma DKIM: Predeterminado.** Lo firma Brevo con su clave, no con una nuestra.
- **DMARC: "no se recomienda usar un dominio de email gratuito".** No hay forma de alinearlo.

El aviso dice que las campañas *pueden* no llegar. No lo bloquea, y hay un dato a favor: los
requisitos duros de Google y Yahoo de 2024 —los que exigen DMARC alineado— aplican a quien
manda **más de 5.000 mensajes por día**. Con menos de 50 destinatarios el listón es más bajo:
que pase SPF **o** DKIM, que haya baja en un clic y que las quejas sean pocas. Todo eso lo
cumple Brevo con su propia autenticación. O sea que no esperamos un rechazo por política; el
riesgo es caer en spam por reputación, que es otra cosa y hay que medirla.

### Confirmado en el primer envío real (1/9/2026)

**Brevo sí reescribe el dominio.** El mail llegó con este remitente:

```
Boletin proyectos ingresados <proparlamentariasenado@11940744.brevosend.com>
```

Mantiene la parte de antes del arroba y el nombre visible, y cambia el dominio por uno suyo.
En la bandeja se ve el nombre; la dirección rara aparece solo si se despliega el encabezado.

Y como ese dominio **sí** es de Brevo y ellos lo firman, todo alinea. Encabezados del mail
que llegó a Gmail:

```
SPF   : PASS con la IP 77.32.148.37
DKIM  : PASS con el dominio 11940744.brevosend.com
DMARC : PASS
```

Entregado nueve segundos después de mandarlo. **La entregabilidad por autenticación está
resuelta sin comprar dominio.** Lo que se pierde es que la dirección no sea reconocible, no
que el mail no llegue.

Mejor todavía: llegó a la **bandeja Prioritarios del correo del Senado**, que es un buzón
corporativo de Microsoft con reglas de organización. Era la prueba más exigente de las tres
y no solo no cayó en spam: el filtro lo marcó como prioritario.

Verificado el 20/8/2026, la política de Gmail hoy es blanda:

```
_dmarc.gmail.com -> v=DMARC1; p=none; sp=quarantine
```

`p=none` significa que todavía no piden tirar a spam lo que no alinea. Es irrelevante igual:
no se llega a esa instancia porque Brevo reescribe el From antes de mandar.

### Lo que se descartó y por qué

- **Comprar un dominio** (diez o quince dólares al año) es la solución de fondo: alinea todo
  y da un remitente reconocible que se puede mudar de proveedor. Queda para cuando haga
  falta infraestructura mejor; por ahora el proyecto va a costo cero.
- **Mandar por el SMTP de Gmail**, sin Brevo, alinea perfecto y es gratis. Se descartó por la
  lista: los mails de los suscriptos son datos personales y este repo es público, así que
  tendrían que vivir en un secret de Actions, sin bajas ni rebotes manejados. En Brevo la
  lista queda del lado de ellos.

### Lo que hay que medir cuando salga el primer envío

- El encabezado `Authentication-Results` de un mail recibido en Gmail: `spf=pass`,
  `dkim=pass`, `dmarc=pass`.
- El puntaje de mail-tester.
- Que llegue a la bandeja, no a spam, en Gmail, Outlook y Yahoo, que filtran distinto.
- Que el mail traiga el encabezado `List-Unsubscribe` con baja en un clic.

## Descartado

- **`fechaMesa`** como fuente: se pierde los expedientes cargados con fecha retroactiva.
  Queda como verificación cruzada si alguna vez hay dudas.
- **Playwright**: la búsqueda anda con HTTP plano. Se ahorra el `playwright install
  --with-deps chromium` de cada corrida.
- **DAE Digital**: `verExp` da lo mismo y más, indexado por expediente en vez de por número
  de DAE.
- **`/micrositios/DatosAbiertos/ExportarListadoAsuntosEntrados/json`**: es solo el índice de
  los PDF por sesión.
- El buscador de Google embebido de la home.

## Notas de trabajo

- **Para empezar en otra máquina:** `git clone` del repo y `pip install -r
  requirements.txt`. Sin eso, `requests`, `xlrd` y `beautifulsoup4` no están y no corre nada
  en local. El padrón y el historial vienen con el repo, así que no hay que rearmar estado.
- Desde la máquina del usuario hay salida de red a `senado.gob.ar`, a
  `raw.githubusercontent.com` y a la API de GitHub, incluidas las corridas de Actions. El
  extractor se puede probar localmente contra el sitio real, sin depender del ciclo
  push → Actions → leer el JSON commiteado.
- El repo local ya está inicializado como git y conectado a `origin`. El usuario se
  autenticó una vez con Git Credential Manager, así que la credencial quedó guardada en
  Windows y los pushes salen sin ventana.
- Los workflows commitean sus resultados al repo: eso cierra el circuito sin copiar y pegar
  informes.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| El Senado cambia las columnas del XLS | El extractor valida el encabezado y corta con `FuenteCambio` en vez de seguir con basura |
| La descarga viene incompleta y se dan de baja cientos de expedientes | Si trae menos de la mitad del padrón, la corrida aborta sin actualizar |
| Fallas silenciosas (devuelve cero y nadie se entera) | Si la exportación viene vacía, la corrida falla en vez de guardar un padrón vacío |
| GitHub desactiva workflows programados tras 60 días sin actividad | El commit diario mantiene el repo activo |
| El Senado carga proyectos con fecha retroactiva | Resuelto: la consulta es por año de expediente, no por fecha |
| Un dia de vuelta de receso trae cientos de altas | Arriba de 80 no se piden fichas, y el cuerpo del issue se recorta con un puntero al archivo completo |
| Mails al spam por remitente sin dominio propio | Se mide en Fase 3 |
| GitHub demora los workflows programados varias horas | El cron va en un minuto no redondo y 37' antes de la hora buscada. Medido: con `0 11` llegó a salir seis horas tarde |
