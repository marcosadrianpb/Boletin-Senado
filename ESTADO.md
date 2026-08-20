# Boletín diario de proyectos del Senado — Estado del proyecto

Última actualización: 20 de agosto de 2026 · **Fase 2 escrita: boletín e issue diario, a la espera del primer día con altas**

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
| Proveedor de mail | Brevo (300/día gratis) con casilla Gmail dedicada verificada. Sin dominio propio por ahora |
| Infraestructura | GitHub Actions, repo público `marcosadrianpb/Boletin-Senado` |
| Lenguaje | Python 3.11 + `requests` + `xlrd` + `beautifulsoup4`. **Sin Playwright** |
| Horario | 8:00 de Buenos Aires, días hábiles (`cron: 0 11 * * 1-5`) |

Los días sin novedades no abren issue: la corrida igual corre, actualiza el padrón y deja
la cuenta en el historial. Si conviene lo contrario, se cambia una condición del workflow.

## Fases

- **Fase 0 — Reconocimiento.** ✅ CERRADA.
- **Fase 1 — Extractor y padrón.** ✅ CERRADA. Corrida 0 y primera comparación, las dos
  verificadas en Actions.
- **Fase 2 — Boletín e issue diario.** ← acá estamos. Escrita y probada contra el sitio
  real; falta verla correr un día con altas de verdad.
- **Fase 3 — Envío por mail.**
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
c6f63b2  Padron del 2026-08-20          <- lo commiteo el workflow
b112fcf  ESTADO.md al dia: corrida 0 hecha y verificada
a84dd06  Ajustes de la corrida 0
d810abc  Padron del 2026-08-19
1bd58af  Fase 1: extraccion por anio de expediente y padron comparable
```

- `src/senado.py` — cliente del buscador. Baja y parsea. No guarda estado.
- `src/padron.py` — el padrón y la comparación. No toca la red.
- `src/actualizar.py` — la corrida diaria: baja, compara, actualiza, escribe novedades.
- `src/boletin.py` — arma el texto del boletín. No toca la red ni el padrón.
- `.github/workflows/actualizar.yml` — corre a las 8:00 AR de lunes a viernes, y a mano.
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

## Próximo paso

Esperar la primera corrida con altas reales —la del próximo día hábil en que el Senado
cargue expedientes— y mirar el issue que abre. Si sale bien, **Fase 3**: el envío por mail
con Brevo, reusando el mismo cuerpo del boletín.

## Arreglado después de la corrida 0

- `upload-artifact` de v4 a v7: el runner avisa que Node 20 está deprecado.
- El archivo de novedades de la línea de base guardaba los 2014 expedientes absorbidos, que
  son los mismos que están en `padron.json`. Ahora guarda solo la cuenta: **de 591 KB a 289
  bytes**. El archivo gordo ya se reemplazó por el chico.
- El resumen del run que escribía `actualizar.py` tenía una tabla con las altas; ahora la
  presentación es toda del boletín y `actualizar.py` deja solo las cuentas de la corrida.

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
