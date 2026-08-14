# Fase 0 - Reconocimiento (v2)

## buscador

- HTTP: 200 | url final: `https://www.senado.gob.ar/parlamentario/parlamentaria/`
- titulo: Honorable Senado de la Nación Argentina

### Formularios
- id=`` name=`` **POST** action=`/parlamentario/parlamentaria/ley`
- id=`` name=`s` **POST** action=`/parlamentario/parlamentaria/exp`
- id=`` name=`s` **POST** action=`/parlamentario/parlamentaria/fechaDada`
- id=`` name=`ingreso2` **POST** action=`/parlamentario/parlamentaria/avanzada`
- id=`` name=`ingreso3` **POST** action=`/parlamentario/parlamentaria/fechaMesa`
- id=`` name=`` **POST** action=`/parlamentario/parlamentaria/orden`
- id=`` name=`ingreso4` **POST** action=`/parlamentario/parlamentaria/comision`
- id=`` name=`ingreso` **POST** action=`/parlamentario/parlamentaria/comiPendientes`
- id=`` name=`ingreso4` **POST** action=`/parlamentario/parlamentaria/comiDicatamen`

### Pestanas
- `INSTITUCIONAL` -> href=`#` target=``
- `Presidencia` -> href=`/presidencia` target=``
- `Autoridades - Organigrama` -> href=`/autoridades` target=``
- `Dependencias del Senado` -> href=`/micrositios/Dependencias` target=``
- `Constitución Nacional` -> href=`https://www.congreso.gob.ar/constitucionNacional.php` target=``
- `Constitución Nacional original de 1853` -> href=`/CN` target=``
- `Reglamento del Senado` -> href=`/reglamento` target=``
- `Enviá tu CV` -> href=`/micrositios/postulante/new` target=``
- `PRENSA` -> href=`#` target=``
- `Gacetillas de Prensa` -> href=`/prensa/eventos` target=``
- `Galería de Fotos` -> href=`/prensa/galeria` target=``
- `Información para Medios` -> href=`/prensa/medios` target=``
- `CONTACTO` -> href=`/FormularioContacto` target=``
- `Senadores` -> href=`/senadores/listados/listaSenadoRes` target=``
- `Proyectos` -> href=`/parlamentario/parlamentaria/` target=``
- `Sesiones` -> href=`/parlamentario/sesiones/busquedaTac` target=``
- `Comisiones` -> href=`/parlamentario/comisiones/?active=permanente` target=``
- `SENADORES` -> href=`/senadores/listados/listaSenadoRes` target=``
- `PROYECTOS` -> href=`/parlamentario/parlamentaria/` target=``
- `SESIONES` -> href=`/parlamentario/sesiones/busquedaTac` target=``
- `COMISIONES` -> href=`/parlamentario/comisiones/?active=permanente` target=``
- `SENADORES -` -> href=`/senadores/listados/listaSenadoRes` target=``
- `PROYECTOS -` -> href=`/parlamentario/parlamentaria/` target=``
- `SESIONES -` -> href=`/parlamentario/sesiones/busquedaTac` target=``
- `COMISIONES` -> href=`/parlamentario/comisiones/?active=permanente` target=``
- `Presidencia` -> href=`/presidencia` target=``
- `Autoridades - Organigrama` -> href=`/autoridades` target=``
- `Dependencias del Senado` -> href=`/micrositios/Dependencias` target=``
- `Constitución Nacional` -> href=`https://www.congreso.gob.ar/constitucionNacional.php` target=``
- `Constitución Nacional original de 1853` -> href=`/CN` target=``
- `Reglamento del Senado` -> href=`/reglamento` target=``
- `Enviá tu CV` -> href=`/micrositios/postulante/new` target=``
- `Noticias` -> href=`/prensa/eventos` target=``
- `Galería de fotos` -> href=`/prensa/galeria` target=``
- `Información para medios` -> href=`/prensa/medios` target=``
- `AGENDA` -> href=`/parlamentario/Agenda/AgendaWeb/14,08,2026` target=``

### Campos utiles (79 de 79 totales)

| tag | type | name | id | placeholder | visible | panel | form |
|---|---|---|---|---|---|---|---|
| input | image | `` | `` |  | SI | 1 |  |
| input | text | `busqueda_proyectos[ley]` | `busqueda_proyectos_ley` |  | no | 1 |  |
| input | image | `` | `type_image` |  | no | 1 |  |
| input | hidden | `busqueda_proyectos[_token]` | `busqueda_proyectos__token` |  | no | 1 |  |
| select |  | `busqueda_proyectos[expedienteLugar]` | `busqueda_proyectos_expedienteLugar` |  | no | 1 |  |
| input | text | `busqueda_proyectos[expedienteNumeroPre]` | `busqueda_proyectos_expedienteNumeroPre` |  | no | 1 |  |
| select |  | `busqueda_proyectos[expedienteNumeroPos]` | `busqueda_proyectos_expedienteNumeroPos` |  | no | 1 |  |
| select |  | `busqueda_proyectos[expedienteTipo]` | `busqueda_proyectos_expedienteTipo` |  | no | 1 |  |
| input | image | `` | `type_image1` |  | no | 1 |  |
| input | hidden | `busqueda_proyectos[_token]` | `busqueda_proyectos__token` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechadada]` | `busqueda_proyectos_fechadada` |  | no | 1 |  |
| input | image | `` | `type_image2` |  | no | 1 |  |
| select |  | `busqueda_proyectos[autor]` | `busqueda_proyectos_autor` |  | no | 1 |  |
| input | text | `busqueda_proyectos[palabra]` | `busqueda_proyectos_palabra` |  | no | 1 |  |
| select |  | `busqueda_proyectos[opcion]` | `busqueda_proyectos_opcion` |  | no | 1 |  |
| input | text | `busqueda_proyectos[palabra2]` | `busqueda_proyectos_palabra2` |  | no | 1 |  |
| select |  | `busqueda_proyectos[comision]` | `busqueda_proyectos_comision` |  | no | 1 |  |
| select |  | `busqueda_proyectos[tipoDocumento]` | `busqueda_proyectos_tipoDocumento` |  | no | 1 |  |
| select |  | `busqueda_proyectos[expedienteLugar]` | `busqueda_proyectos_expedienteLugar` |  | no | 1 |  |
| input | text | `busqueda_proyectos[expedienteNumeroPre]` | `busqueda_proyectos_expedienteNumeroPre` |  | no | 1 |  |
| select |  | `busqueda_proyectos[expedienteNumeroPos]` | `busqueda_proyectos_expedienteNumeroPos` |  | no | 1 |  |
| select |  | `busqueda_proyectos[expedienteTipo]` | `busqueda_proyectos_expedienteTipo` |  | no | 1 |  |
| input | image | `` | `type_image2` |  | no | 1 |  |
| input | hidden | `busqueda_proyectos[_token]` | `busqueda_proyectos__token` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaDesdeMesa][day]` | `busqueda_proyectos_fechaDesdeMesa_day` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaDesdeMesa][month]` | `busqueda_proyectos_fechaDesdeMesa_month` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaDesdeMesa][year]` | `busqueda_proyectos_fechaDesdeMesa_year` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaHastaMesa][day]` | `busqueda_proyectos_fechaHastaMesa_day` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaHastaMesa][month]` | `busqueda_proyectos_fechaHastaMesa_month` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaHastaMesa][year]` | `busqueda_proyectos_fechaHastaMesa_year` |  | no | 1 |  |
| input | image | `` | `type_image3` |  | no | 1 |  |
| input | hidden | `busqueda_proyectos[_token]` | `busqueda_proyectos__token` |  | no | 1 |  |
| input | number | `busqueda_proyectos[ordenDelDiaNumero]` | `busqueda_proyectos_ordenDelDiaNumero` |  | no | 1 |  |
| select |  | `busqueda_proyectos[ordenDelDiaPeriodo]` | `busqueda_proyectos_ordenDelDiaPeriodo` |  | no | 1 |  |
| input | image | `` | `type_image4` |  | no | 1 |  |
| input | hidden | `busqueda_proyectos[_token]` | `busqueda_proyectos__token` |  | no | 1 |  |
| select |  | `busqueda_proyectos[autor]` | `busqueda_proyectos_autor` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaDesde][day]` | `busqueda_proyectos_fechaDesde_day` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaDesde][month]` | `busqueda_proyectos_fechaDesde_month` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaDesde][year]` | `busqueda_proyectos_fechaDesde_year` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaHasta][day]` | `busqueda_proyectos_fechaHasta_day` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaHasta][month]` | `busqueda_proyectos_fechaHasta_month` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaHasta][year]` | `busqueda_proyectos_fechaHasta_year` |  | no | 1 |  |
| input | text | `busqueda_proyectos[palabra]` | `busqueda_proyectos_palabra` |  | no | 1 |  |
| select |  | `busqueda_proyectos[expedienteLugar]` | `busqueda_proyectos_expedienteLugar` |  | no | 1 |  |
| input | text | `busqueda_proyectos[expedienteNumeroPre]` | `busqueda_proyectos_expedienteNumeroPre` |  | no | 1 |  |
| select |  | `busqueda_proyectos[expedienteNumeroPos]` | `busqueda_proyectos_expedienteNumeroPos` |  | no | 1 |  |
| select |  | `busqueda_proyectos[expedienteTipo]` | `busqueda_proyectos_expedienteTipo` |  | no | 1 |  |
| select |  | `busqueda_proyectos[comision]` | `busqueda_proyectos_comision` |  | no | 1 |  |
| input | image | `` | `type_image5` |  | no | 1 |  |
| input | hidden | `busqueda_proyectos[_token]` | `busqueda_proyectos__token` |  | no | 1 |  |
| select |  | `busqueda_proyectos[autor]` | `busqueda_proyectos_autor` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaDesde][day]` | `busqueda_proyectos_fechaDesde_day` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaDesde][month]` | `busqueda_proyectos_fechaDesde_month` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaDesde][year]` | `busqueda_proyectos_fechaDesde_year` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaHasta][day]` | `busqueda_proyectos_fechaHasta_day` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaHasta][month]` | `busqueda_proyectos_fechaHasta_month` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaHasta][year]` | `busqueda_proyectos_fechaHasta_year` |  | no | 1 |  |
| select |  | `busqueda_proyectos[expedienteLugar]` | `busqueda_proyectos_expedienteLugar` |  | no | 1 |  |
| input | text | `busqueda_proyectos[expedienteNumeroPre]` | `busqueda_proyectos_expedienteNumeroPre` |  | no | 1 |  |
| select |  | `busqueda_proyectos[expedienteNumeroPos]` | `busqueda_proyectos_expedienteNumeroPos` |  | no | 1 |  |
| select |  | `busqueda_proyectos[expedienteTipo]` | `busqueda_proyectos_expedienteTipo` |  | no | 1 |  |
| select |  | `busqueda_proyectos[comision]` | `busqueda_proyectos_comision` |  | no | 1 |  |
| input | image | `` | `type_image6` |  | no | 1 |  |
| input | hidden | `busqueda_proyectos[_token]` | `busqueda_proyectos__token` |  | no | 1 |  |
| select |  | `busqueda_proyectos[autor]` | `busqueda_proyectos_autor` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaDesde][day]` | `busqueda_proyectos_fechaDesde_day` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaDesde][month]` | `busqueda_proyectos_fechaDesde_month` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaDesde][year]` | `busqueda_proyectos_fechaDesde_year` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaHasta][day]` | `busqueda_proyectos_fechaHasta_day` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaHasta][month]` | `busqueda_proyectos_fechaHasta_month` |  | no | 1 |  |
| select |  | `busqueda_proyectos[fechaHasta][year]` | `busqueda_proyectos_fechaHasta_year` |  | no | 1 |  |
| select |  | `busqueda_proyectos[expedienteLugar]` | `busqueda_proyectos_expedienteLugar` |  | no | 1 |  |
| input | text | `busqueda_proyectos[expedienteNumeroPre]` | `busqueda_proyectos_expedienteNumeroPre` |  | no | 1 |  |
| select |  | `busqueda_proyectos[expedienteNumeroPos]` | `busqueda_proyectos_expedienteNumeroPos` |  | no | 1 |  |
| select |  | `busqueda_proyectos[expedienteTipo]` | `busqueda_proyectos_expedienteTipo` |  | no | 1 |  |
| select |  | `busqueda_proyectos[comision]` | `busqueda_proyectos_comision` |  | no | 1 |  |
| input | hidden | `busqueda_proyectos[_token]` | `busqueda_proyectos__token` |  | no | 1 |  |
| input | image | `` | `type_image7` |  | no | 1 |  |

### Opciones de los select
- `busqueda_proyectos[expedienteLugar]`: ['=', 'DCD=COMUNIC.DICTAMEN DIPUTADOS', 'CD=CÁMARA DE DIPUTADOS', 'JGM=JEFATURA GABINETE MINISTROS', 'OVD=OFIC.VARIOS H.CÁMARA DIPUTADOS', 'OV=OFICIALES VARIOS']
- `busqueda_proyectos[expedienteNumeroPos]`: ['=', '2026=2026', '2025=2025', '2024=2024', '2023=2023', '2022=2022']
- `busqueda_proyectos[expedienteTipo]`: ['=', 'AC=ACUERDOS', 'C1=C.E. (Art. 101 C.N.)', 'C2=C.E. (Art. 37 Ley 24.156)', 'CA=COMUNICACIONES DE AUDITORÍA', 'CC=COMUNICACIONES DE COMISIONES']
- `busqueda_proyectos[fechadada]`: ['=', '1983-12-15 00:00:00=15-DIC-83', '1983-12-21 00:00:00=21-DIC-83', '1983-12-22 00:00:00=22-DIC-83', '1984-01-11 00:00:00=11-ENE-84', '1984-01-19 00:00:00=19-ENE-84']
- `busqueda_proyectos[autor]`: ['=', '3269=ABAD, ELIAS', '546=ABAD,MAXIMILIANO', '452=ABAL MEDINA,JUAN MANUEL', '564=ABDALA,BARTOLOMÉ ESTEBAN', '371=ABRAMETO,JACOBO ALBERTO']
- `busqueda_proyectos[opcion]`: ['Y=Y', 'O=O']
- `busqueda_proyectos[comision]`: ['=', '76=BANCA DE LA MUJER', '117=BICAMERAL ASESORA DE LA FEDERA', '118=BICAMERAL DE CONTROL DE LOS FO', '315=BICAMERAL DE REFORMA DEL ESTAD', '104=BICAMERAL PERMANENTE DE FISCAL']
- `busqueda_proyectos[tipoDocumento]`: ['=', 'DIC=DICTAMEN', 'EX=EXTRACTO']
- `busqueda_proyectos[expedienteLugar]`: ['=', 'DCD=COMUNIC.DICTAMEN DIPUTADOS', 'CD=CÁMARA DE DIPUTADOS', 'JGM=JEFATURA GABINETE MINISTROS', 'OVD=OFIC.VARIOS H.CÁMARA DIPUTADOS', 'OV=OFICIALES VARIOS']
- `busqueda_proyectos[expedienteNumeroPos]`: ['=', '2026=2026', '2025=2025', '2024=2024', '2023=2023', '2022=2022']
- `busqueda_proyectos[expedienteTipo]`: ['=', 'AC=ACUERDOS', 'C1=C.E. (Art. 101 C.N.)', 'C2=C.E. (Art. 37 Ley 24.156)', 'CA=COMUNICACIONES DE AUDITORÍA', 'CC=COMUNICACIONES DE COMISIONES']
- `busqueda_proyectos[fechaDesdeMesa][day]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaDesdeMesa][month]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaDesdeMesa][year]`: ['2026=26', '2025=25', '2024=24', '2023=23', '2022=22', '2021=21']
- `busqueda_proyectos[fechaHastaMesa][day]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaHastaMesa][month]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaHastaMesa][year]`: ['2026=26', '2025=25', '2024=24', '2023=23', '2022=22', '2021=21']
- `busqueda_proyectos[ordenDelDiaPeriodo]`: ['2026=2026', '2025=2025', '2024=2024', '2023=2023', '2022=2022', '2021=2021']
- `busqueda_proyectos[autor]`: ['=', '3269=ABAD, ELIAS', '546=ABAD,MAXIMILIANO', '452=ABAL MEDINA,JUAN MANUEL', '564=ABDALA,BARTOLOMÉ ESTEBAN', '371=ABRAMETO,JACOBO ALBERTO']
- `busqueda_proyectos[fechaDesde][day]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaDesde][month]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaDesde][year]`: ['2026=26', '2025=25', '2024=24', '2023=23', '2022=22', '2021=21']
- `busqueda_proyectos[fechaHasta][day]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaHasta][month]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaHasta][year]`: ['2026=26', '2025=25', '2024=24', '2023=23', '2022=22', '2021=21']
- `busqueda_proyectos[expedienteLugar]`: ['=', 'DCD=COMUNIC.DICTAMEN DIPUTADOS', 'CD=CÁMARA DE DIPUTADOS', 'JGM=JEFATURA GABINETE MINISTROS', 'OVD=OFIC.VARIOS H.CÁMARA DIPUTADOS', 'OV=OFICIALES VARIOS']
- `busqueda_proyectos[expedienteNumeroPos]`: ['=', '2026=2026', '2025=2025', '2024=2024', '2023=2023', '2022=2022']
- `busqueda_proyectos[expedienteTipo]`: ['=', 'AC=ACUERDOS', 'C1=C.E. (Art. 101 C.N.)', 'C2=C.E. (Art. 37 Ley 24.156)', 'CA=COMUNICACIONES DE AUDITORÍA', 'CC=COMUNICACIONES DE COMISIONES']
- `busqueda_proyectos[comision]`: ['=', '76=BANCA DE LA MUJER', '117=BICAMERAL ASESORA DE LA FEDERA', '118=BICAMERAL DE CONTROL DE LOS FO', '315=BICAMERAL DE REFORMA DEL ESTAD', '104=BICAMERAL PERMANENTE DE FISCAL']
- `busqueda_proyectos[autor]`: ['=', '3269=ABAD, ELIAS', '546=ABAD,MAXIMILIANO', '452=ABAL MEDINA,JUAN MANUEL', '564=ABDALA,BARTOLOMÉ ESTEBAN', '371=ABRAMETO,JACOBO ALBERTO']
- `busqueda_proyectos[fechaDesde][day]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaDesde][month]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaDesde][year]`: ['2026=26', '2025=25', '2024=24', '2023=23', '2022=22', '2021=21']
- `busqueda_proyectos[fechaHasta][day]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaHasta][month]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaHasta][year]`: ['2026=26', '2025=25', '2024=24', '2023=23', '2022=22', '2021=21']
- `busqueda_proyectos[expedienteLugar]`: ['=', 'DCD=COMUNIC.DICTAMEN DIPUTADOS', 'CD=CÁMARA DE DIPUTADOS', 'JGM=JEFATURA GABINETE MINISTROS', 'OVD=OFIC.VARIOS H.CÁMARA DIPUTADOS', 'OV=OFICIALES VARIOS']
- `busqueda_proyectos[expedienteNumeroPos]`: ['=', '2026=2026', '2025=2025', '2024=2024', '2023=2023', '2022=2022']
- `busqueda_proyectos[expedienteTipo]`: ['=', 'AC=ACUERDOS', 'C1=C.E. (Art. 101 C.N.)', 'C2=C.E. (Art. 37 Ley 24.156)', 'CA=COMUNICACIONES DE AUDITORÍA', 'CC=COMUNICACIONES DE COMISIONES']
- `busqueda_proyectos[comision]`: ['=', '76=BANCA DE LA MUJER', '117=BICAMERAL ASESORA DE LA FEDERA', '118=BICAMERAL DE CONTROL DE LOS FO', '315=BICAMERAL DE REFORMA DEL ESTAD', '104=BICAMERAL PERMANENTE DE FISCAL']
- `busqueda_proyectos[autor]`: ['=', '3269=ABAD, ELIAS', '546=ABAD,MAXIMILIANO', '452=ABAL MEDINA,JUAN MANUEL', '564=ABDALA,BARTOLOMÉ ESTEBAN', '371=ABRAMETO,JACOBO ALBERTO']
- `busqueda_proyectos[fechaDesde][day]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaDesde][month]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaDesde][year]`: ['2026=26', '2025=25', '2024=24', '2023=23', '2022=22', '2021=21']
- `busqueda_proyectos[fechaHasta][day]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaHasta][month]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaHasta][year]`: ['2026=26', '2025=25', '2024=24', '2023=23', '2022=22', '2021=21']
- `busqueda_proyectos[expedienteLugar]`: ['=', 'DCD=COMUNIC.DICTAMEN DIPUTADOS', 'CD=CÁMARA DE DIPUTADOS', 'JGM=JEFATURA GABINETE MINISTROS', 'OVD=OFIC.VARIOS H.CÁMARA DIPUTADOS', 'OV=OFICIALES VARIOS']
- `busqueda_proyectos[expedienteNumeroPos]`: ['=', '2026=2026', '2025=2025', '2024=2024', '2023=2023', '2022=2022']
- `busqueda_proyectos[expedienteTipo]`: ['=', 'AC=ACUERDOS', 'C1=C.E. (Art. 101 C.N.)', 'C2=C.E. (Art. 37 Ley 24.156)', 'CA=COMUNICACIONES DE AUDITORÍA', 'CC=COMUNICACIONES DE COMISIONES']
- `busqueda_proyectos[comision]`: ['=', '76=BANCA DE LA MUJER', '117=BICAMERAL ASESORA DE LA FEDERA', '118=BICAMERAL DE CONTROL DE LOS FO', '315=BICAMERAL DE REFORMA DEL ESTAD', '104=BICAMERAL PERMANENTE DE FISCAL']

### Botones
- `Toggle navigation` id=`` type=button onclick=``
- `×` id=`` type=button onclick=``
- `Cerrar` id=`` type=button onclick=``

### Enlaces de exportacion / descarga
- `Datos abiertos` -> `/micrositios/DatosAbiertos/` onclick=``

## Campos que aparecen al activar cada pestana

pestanas encontradas: 0

## asuntos_entrados

- HTTP: 200 | url final: `https://www.senado.gob.ar/parlamentario/sesiones/asuntosEnt`
- titulo: Honorable Senado de la Nación Argentina

### Formularios
- id=`` name=`` **POST** action=`/parlamentario/sesiones/asuntosResultado`

### Pestanas
- `INSTITUCIONAL` -> href=`#` target=``
- `Presidencia` -> href=`/presidencia` target=``
- `Autoridades - Organigrama` -> href=`/autoridades` target=``
- `Dependencias del Senado` -> href=`/micrositios/Dependencias` target=``
- `Constitución Nacional` -> href=`https://www.congreso.gob.ar/constitucionNacional.php` target=``
- `Constitución Nacional original de 1853` -> href=`/CN` target=``
- `Reglamento del Senado` -> href=`/reglamento` target=``
- `Enviá tu CV` -> href=`/micrositios/postulante/new` target=``
- `PRENSA` -> href=`#` target=``
- `Gacetillas de Prensa` -> href=`/prensa/eventos` target=``
- `Galería de Fotos` -> href=`/prensa/galeria` target=``
- `Información para Medios` -> href=`/prensa/medios` target=``
- `CONTACTO` -> href=`/FormularioContacto` target=``
- `Senadores` -> href=`/senadores/listados/listaSenadoRes` target=``
- `Proyectos` -> href=`/parlamentario/parlamentaria/` target=``
- `Sesiones` -> href=`/parlamentario/sesiones/busquedaTac` target=``
- `Comisiones` -> href=`/parlamentario/comisiones/?active=permanente` target=``
- `SENADORES` -> href=`/senadores/listados/listaSenadoRes` target=``
- `PROYECTOS` -> href=`/parlamentario/parlamentaria/` target=``
- `SESIONES` -> href=`/parlamentario/sesiones/busquedaTac` target=``
- `COMISIONES` -> href=`/parlamentario/comisiones/?active=permanente` target=``
- `SENADORES -` -> href=`/senadores/listados/listaSenadoRes` target=``
- `PROYECTOS -` -> href=`/parlamentario/parlamentaria/` target=``
- `SESIONES -` -> href=`/parlamentario/sesiones/busquedaTac` target=``
- `COMISIONES` -> href=`/parlamentario/comisiones/?active=permanente` target=``
- `Senado TV en vivo` -> href=`/parlamentario/sesiones/enVivo` target=``
- `Boletín de Novedades` -> href=`/parlamentario/sesiones/` target=``
- `Versiones Taquigráficas` -> href=`/parlamentario/sesiones/busquedaTac` target=``
- `Dae Digital` -> href=`/parlamentario/DAEDIGITAL/` target=``
- `Lista de Asuntos Entrados` -> href=`#1` target=``
- `Plenario de Labor Parlamentaria` -> href=`/parlamentario/parlamentaria/actas` target=``
- `Votaciones` -> href=`/votaciones/actas` target=``
- `Presidencia` -> href=`/presidencia` target=``
- `Autoridades - Organigrama` -> href=`/autoridades` target=``
- `Dependencias del Senado` -> href=`/micrositios/Dependencias` target=``
- `Constitución Nacional` -> href=`https://www.congreso.gob.ar/constitucionNacional.php` target=``

### Campos utiles (10 de 10 totales)

| tag | type | name | id | placeholder | visible | panel | form |
|---|---|---|---|---|---|---|---|
| select |  | `busqueda_proyectos[fechaDesde][day]` | `busqueda_proyectos_fechaDesde_day` |  | SI | 1 |  |
| select |  | `busqueda_proyectos[fechaDesde][month]` | `busqueda_proyectos_fechaDesde_month` |  | SI | 1 |  |
| select |  | `busqueda_proyectos[fechaDesde][year]` | `busqueda_proyectos_fechaDesde_year` |  | SI | 1 |  |
| select |  | `busqueda_proyectos[fechaHasta][day]` | `busqueda_proyectos_fechaHasta_day` |  | SI | 1 |  |
| select |  | `busqueda_proyectos[fechaHasta][month]` | `busqueda_proyectos_fechaHasta_month` |  | SI | 1 |  |
| select |  | `busqueda_proyectos[fechaHasta][year]` | `busqueda_proyectos_fechaHasta_year` |  | SI | 1 |  |
| input | text | `busqueda_proyectos[palabra]` | `busqueda_proyectos_palabra` |  | SI | 1 |  |
| select |  | `busqueda_proyectos[opcion]` | `busqueda_proyectos_opcion` |  | SI | 1 |  |
| input | text | `busqueda_proyectos[palabra2]` | `busqueda_proyectos_palabra2` |  | SI | 1 |  |
| input | image | `` | `` |  | SI | 1 |  |

### Opciones de los select
- `busqueda_proyectos[fechaDesde][day]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaDesde][month]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaDesde][year]`: ['2026=26', '2025=25', '2024=24', '2023=23', '2022=22', '2021=21']
- `busqueda_proyectos[fechaHasta][day]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaHasta][month]`: ['1=1', '2=2', '3=3', '4=4', '5=5', '6=6']
- `busqueda_proyectos[fechaHasta][year]`: ['2026=26', '2025=25', '2024=24', '2023=23', '2022=22', '2021=21']
- `busqueda_proyectos[opcion]`: ['Y=Y', 'O=O']

### Botones
- `Toggle navigation` id=`` type=button onclick=``
- `descargar` id=`` type=button onclick=``
- `descargar` id=`` type=button onclick=``
- `descargar` id=`` type=button onclick=``
- `descargar` id=`` type=button onclick=``
- `descargar` id=`` type=button onclick=``
- `descargar` id=`` type=button onclick=``
- `descargar` id=`` type=button onclick=``
- `descargar` id=`` type=button onclick=``
- `descargar` id=`` type=button onclick=``
- `descargar` id=`` type=button onclick=``

### Enlaces de exportacion / descarga
- `` -> `/micrositios/DatosAbiertos/ExportarListadoAsuntosEntrados/Excel` onclick=``
- `` -> `/micrositios/DatosAbiertos/ExportarListadoAsuntosEntrados/json` onclick=``
- `descargar` -> `/parlamentario/parlamentaria/sesionordinaria%2016-07-26.pdf/downloadEntrados` onclick=``
- `descargar` -> `` onclick=``
- `descargar` -> `/parlamentario/parlamentaria/sesionordinaria04-06-2026.pdf/downloadEntrados` onclick=``
- `descargar` -> `` onclick=``
- `descargar` -> `/parlamentario/parlamentaria/sesionordinaria14-05-2026.pdf/downloadEntrados` onclick=``
- `descargar` -> `` onclick=``
- `descargar` -> `/parlamentario/parlamentaria/sesionordinaria09-04-2026-.pdf/downloadEntrados` onclick=``
- `descargar` -> `` onclick=``
- `descargar` -> `/parlamentario/parlamentaria/sesionordinaria18-03-2026.pdf/downloadEntrados` onclick=``
- `descargar` -> `` onclick=``
- `descargar` -> `/parlamentario/parlamentaria/sesionespecial27-02-2026.pdf/downloadEntrados` onclick=``
- `descargar` -> `` onclick=``
- `descargar` -> `/parlamentario/parlamentaria/sesionespecial26-02-2026.pdf/downloadEntrados` onclick=``
- `descargar` -> `` onclick=``
- `descargar` -> `/parlamentario/parlamentaria/sesionpreparatoria24-02-26.pdf/downloadEntrados` onclick=``
- `descargar` -> `` onclick=``
- `descargar` -> `/parlamentario/parlamentaria/sesionespecialAGN24-02-2026.pdf/downloadEntrados` onclick=``
- `descargar` -> `` onclick=``
- `descargar` -> `/parlamentario/parlamentaria/sesionespecial11-02-26.pdf/downloadEntrados` onclick=``
- `descargar` -> `` onclick=``
- `Datos abiertos` -> `/micrositios/DatosAbiertos/` onclick=``

## Peticiones a senado.gob.ar

- `GET https://www.senado.gob.ar/parlamentario/parlamentaria/` -> 200 (text/html; charset=UTF-8)
- `GET https://l.sharethis.com/pview?event=pview&hostname=www.senado.gob.ar&location=%2Fparlamentario%2Fparlamentaria%2F&product=sop&url=https%3A%2F%2Fwww.senado.gob.ar%2Fparlamentario%2Fparlamentaria%2F&source=sharethis.js&fcmp=false&fcmpv2=false&has_segmentio=false&title=Honorable%20Senado%20de%20la%20Na` -> 204 ()
- `GET https://www.senado.gob.ar/parlamentario/sesiones/asuntosEnt` -> 200 (text/html; charset=UTF-8)
- `GET https://l.sharethis.com/pview?event=pview&hostname=www.senado.gob.ar&location=%2Fparlamentario%2Fsesiones%2FasuntosEnt&product=sop&url=https%3A%2F%2Fwww.senado.gob.ar%2Fparlamentario%2Fsesiones%2FasuntosEnt&source=sharethis.js&fcmp=false&fcmpv2=false&has_segmentio=false&title=Honorable%20Senado%20de` -> 204 ()