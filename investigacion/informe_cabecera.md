# Hallazgos de la investigación genealógica

*Contraste del árbol Álvarez Ruiz con fuentes publicadas, noviembre de 2026.*

Este informe recoge el resultado de contrastar los datos extraídos de los cuadros originales (el árbol de Manuel Salvador Álvarez Ruiz y el de María Teresa Ruiz Maya) con fuentes publicadas en internet. Los datos del documento original **no se modificaron**: todo lo hallado vive en una capa aparte, [`contenido/investigacion.json`](../contenido/investigacion.json), que el script `scripts/build_site.py` aplica al generar la web y el libro. Cada corrección guarda el valor original, y la web y el libro distinguen lo que viene del documento de lo que viene de la investigación.

## 1. Método

1. **Revisión automática de los datos** (`docs/data/familia.json`) con scripts:
   - posibles duplicados (mismo nombre y mismos padres o mismo cónyuge);
   - nombres partidos o con lugares pegados («de Andrade Primer Alcalde», «Medellín», «Haro Suárez», «Juan García Gómez Santa Fe»…);
   - años imposibles (hijos mayores que sus padres, padres 70 o más años mayores);
   - personas con varios cónyuges.
2. **Comprobación en el cuadro original.** Para cada sospecha se leyó el texto del PDF del cuadro con sus coordenadas. Así se distinguen los errores de la lectura automática (tipo «extracción», que se corrigen siempre) de los datos que trae el propio documento.
3. **Búsqueda en fuentes externas.** Se priorizaron los ancestros antioqueños de los siglos XVI a XIX, los pobladores y personajes notables, la cadena medieval de María Teresa y las afirmaciones de `contenido/historia.json`. Las páginas que exigen JavaScript (Real Academia de la Historia) se leyeron con Edge sin interfaz. Los PDF se descargaron y se extrajo su texto.
4. **Cruce con el catálogo de mortuorias del Archivo Histórico de Antioquia.** La British Library (proyecto EAP1531) catalogó y digitalizó los expedientes de 1606-1750. Se descargaron los títulos y fechas de los 727 expedientes de los tomos 193 a 324 y se cruzaron con los nombres del árbol.
5. **Clasificación.**
   - **CONFIRMADO**: fuente seria, o varias que coinciden. Se aplica al árbol.
   - **PROBABLE**: indicio razonable, como un árbol de usuario, un catálogo de archivo sin leer el documento o una coincidencia de nombre y fecha. Queda solo como nota.
   - **EN CONFLICTO**: las fuentes difieren. Se muestran las dos versiones y el árbol conserva la del documento.
6. **Privacidad.** No se investigó ni se publicó ningún dato nuevo de personas vivas ni de nacidos después de 1930 aproximadamente. Eso incluye a los once hijos, a Manuel Salvador y a María Teresa, y a sus hermanos. La búsqueda se centró en ancestros fallecidos, en su mayoría de los siglos XVI a XVIII.

## 2. Fuentes consultadas

**Consultadas y útiles**
- Gabriel Arango Mejía, *Genealogías de Antioquia y Caldas*: transcripción de la familia Jaramillo (n.º 182, págs. 493-518) en la biblioteca de la Universidad Brigham Young. Es la fuente principal de las correcciones de la línea Naranjo.
- Revista de la Universidad Pontificia Bolivariana:
  - Nazario Bernal, «Divagaciones genealógicas sobre los Arangos» (cita a Arango Mejía);
  - el mismo autor sobre los Jaramillo;
  - Emilio Robledo, sobre Arango Mejía;
  - Fernando Panesso Posada, «Familias de Antioquia».
- Reinaldo Ágredo Tobar (comp.), *Ancestros de Diego Álvarez de Castrillón* (2014). Se basa en el testamento de 1611, en Arango Mejía y en María Emma Escovar Uribe.
- British Library, Endangered Archives Programme EAP1531: catálogo de mortuorias del Archivo Histórico de Antioquia, 1606-1750.
- Real Academia de la Historia, Diccionario Biográfico: Juan Ponce de León (II conde de Arcos), Pedro Ponce de León (I conde de Arcos), Pedro Ponce de León «el Viejo» y Pedro Ponce de León, ricohombre.
- «Moradas para una estirpe: la familia Ponce de León en Jerez de la Frontera» (El Barroco Jerezano, 2022). Usa el testamento de Eutropio Ponce de León (1510) y la obra de Moreno de Guerra.
- John Alejandro Ricaurte Cartagena, *Guía de los vascos en Antioquia, siglos XVI y XVII* (Gobierno Vasco).
- Wikipedia en español:
  - Aldonza Alfonso de León, Fernán Pérez Ponce de León, Pedro Ponce de León el Viejo, Pedro Ponce de Cabrera, Alfonso IX, Guzmán el Bueno;
  - Fruela II, Ramiro III, Ordoño Ramírez el Ciego, Hermenegildo Gutiérrez, Osorio Gutiérrez, Gatón del Bierzo, Bermudo I;
  - Historia de Medellín, Álvarez (apellido), Álvar Fáñez, Albares de la Ribera, Arma (Caldas), Copacabana, Coltejer, Ferrocarril de Antioquia.
- Buber's Basque Page, *Basque Families of Antioquia* (familia Arteaga).
- Genealogía Familiar (genealogiafamiliar.net), Eutropio Ponce de León. Es un árbol de usuario.

**No se pudieron consultar o solo se vieron en el extracto del buscador**
- **FamilySearch**: los árboles y los registros parroquiales piden cuenta; los libros de Medellín y San Cristóbal del siglo XIX solo están como imágenes. Solo se vio una biografía pública, la de Bartolomé Sánchez Torreblanca, y se usó como PROBABLE.
- **Geneanet**: bloquea la lectura automática (Cloudflare, error 403). Sus árboles solo se vieron en los extractos del buscador.
- **Geni**: la herramienta de lectura bloqueó el dominio y Edge sin interfaz devolvió páginas vacías.
- **YourRoots (Genomelink)** exige cuenta, y **MyHeritage** solo muestra páginas de nombres.
- **Genealogías de Antioquia y Caldas completas**: no hay copia abierta en línea. Solo se encontró la sección J en la transcripción de BYU.
- Los **expedientes del Archivo Histórico de Antioquia** están digitalizados en la British Library, pero solo se leyó el catálogo (título y fecha), no los manuscritos.
- **PARES** y el **Archivo General de la Nación** no dieron resultados pertinentes en las búsquedas.
- Las búsquedas en el **repositorio de la Universidad de Antioquia** y en la **Biblioteca Nacional de Colombia** no devolvieron documentos sobre estas familias.

## 3. Principales hallazgos

### El parentesco Ruiz Velásquez (H01)
Las dos investigaciones originales, hechas por separado, coinciden: Trinidad (madre de Manuel Salvador) y Dolores (abuela de María Teresa) eran hijas de José María Ruiz Moreno y María Mercedes Velásquez Restrepo, con la misma ascendencia en las dos ramas. **No se encontró una fuente externa abierta que lo confirme.** Los registros del siglo XIX están en FamilySearch, pero solo para usuarios con cuenta. Queda como PROBABLE.

### Línea Álvarez
- **Juan Manuel Álvarez del Pino nació en 1689, no en 1600** (H02, corregido). El dato sale del propio texto del linaje: 1600 es imposible.
- **Diego Álvarez del Pino (hijo)**, esposo de Beatriz Tabares, estaba duplicado (H03). El Archivo Histórico de Antioquia conserva su **mortuoria de 1661**, con testamento, inventario y avalúo.
- Se confirma la pareja **Gregorio Álvarez del Pino – Juana Gabriela García de Ordaz** por el matrimonio de su hija Alfonsa en Medellín en 1695 (H05).
- **Bartolomé Sánchez Torreblanca**, conquistador y compañero de Robledo en la fundación de Antioquia, estaba duplicado (H31). Tuvo dos uniones.
- Se unieron duplicados de la extracción: José Luis Gómez Poblete, Juan Francisco González de Noriega y su esposa.

### Línea Naranjo (la que más cambió)
- **Alonso Jaramillo de Andrade y Céspedes** (H07-H10): la extracción había inventado una generación falsa con fragmentos de su título («de Andrade Primer Alcalde», «Céspedes Mayor de»). Ahora está enlazado a sus padres verdaderos, Juan Jaramillo de Andrade (bautizado en 1611) y Ana de Céspedes y Guzmán. Arango Mejía documenta su **matrimonio en Aná el 8 de mayo de 1672** con **Jacinta de Molina**, hija de Carlos de Molina y Beatriz Beltrán del Castillo, y una segunda esposa, **Catalina de Arango**, que se añadió al árbol. Su título de «primer alcalde de Medellín en 1675» queda EN CONFLICTO: Wikipedia da otros nombres para los primeros cargos.
- **José Eugenio Arango Vélez** era hijo de Esteban Arango y Gertrudis Vélez, no de Antonio Valdés de Arango y Olaya de Zafra, que eran sus abuelos (H16). Nació en julio de 1697 y se casó en Rionegro el 19 de mayo de 1715.
- **Cuadro 17A** (H13, H13B): faltaba una generación, la de Juan García Burgos e Isabel Gómez Gómez, y los padres de María Luisa Jaramillo Rodríguez estaban cambiados. Se añadieron las dos personas que faltaban, y con ellas vuelve al árbol toda la ascendencia Gómez de Salazar, que había quedado suelta.
- **Diego Álvarez de Castrillón**, asturiano de Boal, testó en Arma en 1611 (H29). Tuvo **un solo hijo Mateo**, nacido en Arma el 27 de septiembre de 1600; la extracción lo había convertido en tres personas (H28).

### Antepasados de los dos lados
- **Carlos de Molina y Beatriz Beltrán del Castillo** estaban en un cuadro de cada rama sin unir (H15). Ahora son antepasados de ambos: por Úrsula Molina en la rama de Manuel Salvador y por Jacinta de Molina en la de María Teresa.

### Rama medieval de María Teresa
- **Confirmado con la RAH y Wikipedia:**
  - Alfonso IX de León → Aldonza Alfonso → Pedro Ponce de Cabrera → Fernán Pérez Ponce de León → los señores de Marchena → Pedro Ponce de León, I conde de Arcos → Juan Ponce de León, II conde de Arcos, nacido hacia 1400 (H41, H42).
  - Eutropio Ponce de León es hijo de Juan Ponce de León; se casó con Catalina de Vera y su hijo Francisco se casó con Isabel Riquel (H45).
- **Correcciones de extracción:**
  - Pedro Ponce de León y Haro tenía como «madre» una persona inexistente, «Haro Suárez» (H43).
  - Sancho I el Craso estaba partido en dos personas, una de ellas llamada «León» (H48).
- **Dudas y conflictos:**
  - El suegro de Eutropio es el comendador Pedro de Vera «el Bermejo», no el conquistador de Canarias (H46).
  - El padre del I conde de Arcos murió en 1374 y no en 1387 (H44).
  - **El empalme entre Antioquia y los Ponce de León** (de Pedro Ponce de León y Riquelme al capitán Francisco de Guzmán) no aparece en ninguna fuente y tiene fechas imposibles. Es el eslabón más débil (H47).
  - Aznar Fróilaz como hijo de Fruela II es una filiación despreciada por los historiadores (H50).
  - Los condes gallegos del siglo IX llevan filiaciones conjeturales (H51).
  - **Los visigodos** (Flavio Teudo, Atanarico, la «princesa goda Arquilona») son legendarios (H52).

### Historia y apellido
- **Álvarez es un patronímico** («hijo de Álvaro») con muchos troncos distintos, no un solo linaje (H53). Además:
  - Nava y Castropol son concejos distintos.
  - La relación de Álvar Fáñez con el Cid es literaria y no consta que fuera soriano.
  - La Albares del Bierzo sí existe: es Albares de la Ribera.
- La tradición de la **maquinaria de Coltejer traída desde El Limón** encaja con 1920-1929, entre la llegada del tren a El Limón y la apertura del túnel de La Quiebra. No encaja con la fundación de la empresa, en 1907 (H54).

## 4. Correcciones aplicadas

Se aplicaron 21 hallazgos. Las correcciones más importantes:
- **29 personas eliminadas.** Eran duplicados unidos con su gemelo o fragmentos de nombres partidos por la extracción. Sus nombres quedan como variantes de la persona correspondiente.
- **3 personas añadidas:**
  - Catalina de Arango Zafra, segunda esposa de Alonso Jaramillo de Andrade, según Arango Mejía;
  - Juan García Burgos e Isabel Gómez Gómez, del cuadro 17A, que la extracción había saltado.
- **Datos cambiados:**
  - años: Juan Manuel Álvarez del Pino, José Eugenio Arango y Pedro Ponce de León y Haro;
  - nombres: Alonso Jaramillo de Andrade y Céspedes, Jacinta de Molina y Toledo, Jerónima Peláez Echeverri, Juan García Gómez, Sancho I el Craso y María de Ayala Suárez;
  - lugar: Mateo de Castrillón, nacido en Arma;
  - padres de 8 personas.
- **Cifras resultantes:**
  - antepasados de ambos: de 526 a 538;
  - antepasados distintos: de 1062 a 1055;
  - personas conectadas al árbol: de 1083 a 1076, porque desaparecen duplicados y fragmentos aunque se reconectaron otras 14;
  - personas en total: de 1137 a 1111;
  - generaciones: de 41 a 39, porque se eliminaron dos generaciones falsas (H07 y H43).

El reparto entre las líneas Ruiz y Naranjo cambió. Al corregir los padres de José Eugenio Arango, la ascendencia Arango-Zafra-Castrillón pasa a alcanzarse primero desde la línea Ruiz, por Fernando Arango Vélez.

## 5. Dudas abiertas
- El parentesco Ruiz Velásquez y los Ruiz, Naranjo y Maya del siglo XIX. Hacen falta los registros parroquiales de Medellín, San Cristóbal y Palmitas en FamilySearch, con cuenta.
- La **línea Vélez** (Rosalía Vélez Rivera) sigue sin ascendencia: no se encontró nada.
- Ignacio Javier y José Ignacio Vélez de Toro: ¿son la misma persona (H38)? La misma pregunta vale para los dos matrimonios de Gertrudis Benítez Colmenero y de Juan Ruiz de la Parra (H39).
- Hay años que parecen de muerte y no de nacimiento (H21, H23, H40).
- El título exacto de Alonso Jaramillo de Andrade en 1675 (H10).
- El empalme medieval (H47) y los eslabones altomedievales y visigodos (H51, H52).
- **Pistas en el Archivo Histórico de Antioquia:** las mortuorias digitalizadas que coinciden con nombres del árbol (HA01-HA15, H33-H37, H56) pueden confirmar padres, cónyuges e hijos si se leen los manuscritos.

## 6. Hallazgos uno por uno

La lista completa, con texto y fuentes, se genera a partir de `contenido/investigacion.json`:
