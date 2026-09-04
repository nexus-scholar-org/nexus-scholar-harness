---
workspace_id: SCI-001114
doi: 10.17268/sci.agropecu.2026.020
title: Detection of late blight in potato leaves using drone images and Deep Learning
  techniques
authors:
- family_name: Cairampoma
  given_name: J. A.
  orcid: null
- family_name: Gamarra-Gamarra
  given_name: Delia
  orcid: null
- family_name: Dionisio
  given_name: F. E.
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T01:48:55.268751+00:00'
---

# Detection of late blight in potato leaves using drone images and Deep Learning techniques

Scientia Agropecuaria 17(2): 293-303 (2026)                           Cairampoma et al.

SCIENTIA   AGROPECUARIA

Facultad de Ciencias

Trujillo   Scientia Agropecuaria

Agropecuarias

Universidad Nacional de

Web page: http://revistas.unitru.edu.pe/index.php/scientiaagrop

RESEARCH ARTICLE

Detection of late blight in potato leaves using drone images and Deep Learning  techniques

Detección del tizón tardío en folíolos de papa usando imágenes tomadas con dron y  técnicas de Deep Learning

J. A. Cairampoma1* ; Delia Gamarra-Gamarra1 ; F. E. Dionisio1     1 Universidad Nacional del Centro del Perú, Av. Mariscal Castilla 3909, Huancayo, Perú.     * Corresponding author: jcairampoma@uncp.edu.pe (J. Cairampoma).    Received: 4 July 2025. Accepted: 26 January 2026. Published: 16 February 2026.


## Abstract

Phytophthora infestans causes one of the most devastating diseases of the potato crop, also known as late blight. Since early identification 
of this pathogen is crucial for the effective control of the disease, this study aimed to propose an automated methodology for the 
identification of its lesions in potato leaflets, using convolutional neural networks called “Mask R-CNN”. The evaluations were carried out 
during the rainy season, in crops conducted by farmers in the locality of Huasahuasi, in the central Andes of Peru. One hundred 
photographs (5472 × 3078 pixels) were taken with a Phantom 4 Pro unmanned aerial vehicle (UAV) at an altitude of 3 m in crops with a 
late blight incidence between 2 and 3. The images were divided into four parts and then passed thorough quality control, resulting in 200 
photos (1825 × 1369 pixels). Of the total, 75% was used for model training and 25% for model validation. The models were evaluated 
under real conditions, using metrics such as accuracy and recall. It was determined that the Mask R-CNN neural network, based on the 
ResNet 101 deep neural network architecture, offers acceptable accuracy and effectiveness (73.5%) in the identification of late blight lesions 
at the leaflet level. This methodology constitutes a significant contribution to precision agriculture in the Andes, validating a non-invasive 
tool capable of overcoming the topographical limitations of the area. Its practical application would optimize the use of fungicides through 
targeted detection, thereby promoting more sustainable and profitable potato production systems for local farmers.

Keywords: Late blight detection; Unmanned aerial vehicle (UAV); Dron; Convolutional neural network; Mask R-CNN; Potato leaflets.

Resumen  Phytophthora infestans causa una de las enfermedades más devastadoras del cultivo de papa, también conocida como tizón tardío. Dado  que la identificación temprana de este patógeno es crucial para el control efectivo de la enfermedad, este estudio tuvo como objetivo  proponer una metodología automatizada para la identificación de sus lesiones en foliolos de papa, utilizando redes neuronales  convolucionales llamadas "Mask R-CNN". Las evaluaciones se llevaron a cabo durante la temporada de lluvias, en cultivos realizados por  agricultores en la localidad de Huasahuasi, en los Andes centrales del Perú. Se tomaron cien fotografías (5472 × 3078 píxeles) con un  vehículo aéreo no tripulado (UAV) Phantom 4 Pro a una altitud de 3 m en cultivos con una incidencia de tizón tardío entre 2 y 3. Las  imágenes se dividieron en cuatro partes y luego pasaron un riguroso control de calidad, dando como resultado 200 fotos (1825 × 1369  píxeles). Del total, el 75% se utilizó para el entrenamiento del modelo y el 25% para su validación. Los modelos se evaluaron en condiciones  reales, utilizando métricas como la precisión y la recuperación. Se determinó que la red neuronal Mask R-CNN, basada en la arquitectura  de red neuronal profunda ResNet 101, ofrece una precisión y efectividad aceptables (73,5%) en la identificación de lesiones de tizón tardío  a nivel de foliolo. Esta metodología constituye una contribución significativa a la agricultura de precisión en los Andes, al validar una  herramienta no invasiva capaz de superar las limitaciones topográficas de la zona. Su aplicación práctica optimizaría el uso de fungicidas  mediante la detección dirigida, promoviendo así sistemas de producción de papa más sostenibles y rentables para los agricultores locales.

Palabras clave: Detección del tizón tardío; Dron; Red neuronal convolucional; Mask R-CNN; Folíolos de papa.

DOI: https://doi.org/10.17268/sci.agropecu.2026.020

Cite this article:  Cairampoma, J. A., Gamarra-Gamarra, D., & Dionisio, F. E. (2026). Detección del tizón tardío en folíolos de papa usando imágenes  tomadas con dron y técnicas de Deep Learning. Scientia Agropecuaria, 17(2), 293-303.     1. Introducción  Phytophthora infestans causa la enfermedad co- múnmente llamada tizón tardío o rancha, es  considerada la enfermedad más destructiva a nivel

mundial del cultivo de papa (Ivanov et al., 2021). En  el Perú, es la principal limitación en la producción  de este tubérculo, ya que reduce drásticamente su  rendimiento. Esta enfermedad es más prevalente y

-293-

Scientia Agropecuaria 17(2): 293-303 (2026)                           Cairampoma et al.

dañina entre los 2800 y 3500 m s. n. m. (Zevallos et  al., 2021). Su manejo resulta particularmente  desafiante debido a las condiciones climáticas y  otros factores (Perez et al., 2022). Dado que la papa  es un alimento básico y una de las principales fuen- tes de ingresos para los agricultores en las zonas  altoandinas (Devaux et al., 2020), es necesario  desarrollar estrategias eficaces para controlar esta  enfermedad.  Los síntomas iniciales se manifiestan en los folíolos  en forma de pequeñas manchas irregulares  (Berhan, 2021). En condiciones ambientales propi- cias adquiere un color que va desde castaño a ma- rrón oscuro. Estas lesiones se delimitan claramente  de las áreas sanas (Duarte-Carvajalino et al., 2018).  Las lesiones pueden extenderse por toda la super- ficie foliar y avanzar a través del peciolo hacia el  tallo. En algunos cultivares se observa un halo verde  claro alrededor del tejido necrótico. Asimismo,  pueden manifestarse en hojas y tallos pocas horas  después de la infección, dependiendo de las condi- ciones ambientales y la susceptibilidad del  hospedante (Majeed et al., 2017).   La evaluación tradicional de esta enfermedad se  basa en la medición de la incidencia y la severidad  en el campo. Este método directo presenta varias  desventajas: es invasivo y puede contribuir a la di- seminación de la enfermedad, requiere personal  técnico especializado, se limita a muestrear áreas  reducidas del cultivo, lo que compromete su efica- cia y representatividad. En las zonas altoandinas del  Perú, como en Huasahuasi, donde las condiciones  agroclimáticas y edáficas son ideales para el cultivo  de papa y también para el desarrollo del hongo P.  infestans. La evaluación tradicional resulta poco  práctica debido a lo agreste de la zona y sus altas  pendientes. Por lo tanto, es esencial buscar  métodos de evaluación menos invasivos y más  eficaces que puedan adaptarse a las condiciones  particulares de estas regiones.  Recientemente, se han propuesto técnicas novedo- sas para la identificación de enfermedades en  diversos cultivos. Entre estas innovaciones destaca  la visión por computadora, una técnica basada en  algoritmos de aprendizaje profundo (DL, Deep  Learning) (Matsuo et al., 2022) que forman parte de  las redes neuronales artificiales (ANN, por sus siglas  en inglés). Estas redes simulan la estructura y el pro- ceso neuronal humano con el objetivo de recono- cer patrones (Baba, 2024; Bai et al., 2021). La  literatura más actual de 2025 evidencia un avance  significativo hacia modelos más robustos y ligeros  capaces de operar en entornos complejos. Por  ejemplo, Alanazi (2025) demostraron la eficacia de

la arquitectura YOLOv10 en la agricultura de preci- sión, logrando detecciones en tiempo real con alta  fidelidad para enfermedades foliares. Asimismo, MK  & Matharasi (2025) presentaron mejoras significati- vas en la predicción de enfermedades de la papa  utilizando técnicas avanzadas de Deep Learning. En  el caso específico de la papa, estudios recientes han  comenzado a integrar modelos híbridos (como Ef- ficientNet combinado con Vision Transformers) que  superan en precisión a las redes convencionales  (Sinamenye et al., 2025).   Por ejemplo, Yu et al. (2022) usaron DL para el re- conocimiento automático de enfermedades en ho- jas de soja, logrando resultados muy satisfactorios.  Este  algoritmo  también  fue  usado  por  Kunduracioglu & Pacal (2024) en el diagnóstico de  enfermedades de la uva. Ganesh et al. (2019) y Yu  et al. (2019) lo usaron en la caracterización de la ca- lidad y madurez de los frutales. También se han  mejorado las técnicas de monitoreo en el campo  mediante el uso de diversos equipos como las cá- maras fotográficas convencionales, cámaras hiper- espectrales, el uso de drones o satelitales (Abbas et  al., 2023; Jadhav et al., 2023; Wang et al., 2021).  En este contexto, el presente estudio tuvo como  objetivo proponer una nueva metodología auto- matizada para la identificación de síntomas del P.  infestans en folíolos de papa en condiciones de cul- tivos de agricultores de la localidad de Huasahuasi,  basada en el uso de DRON para el muestreo y la  aplicación de técnicas de DL para la detección de  las lesiones. Esta técnica tiene el potencial de su- perar las limitaciones de los métodos tradicionales  al ofrecer una evaluación no invasiva, eficiente y a  gran escala, adaptada a las condiciones específicas  de la topografía agreste y las particularidades agro- climáticas de la zona de estudio.    2. Metodología

2.1. Área de estudio

El presente estudio se realizó en campos de agri- cultores del agroecosistema de Huasahuasi, situado  en la provincia de Tarma, en la región de Junín  (Figura 1). Geográficamente, se ubica en los Andes  centrales del Perú, en el flanco oriental, entre las la- titudes sur de 11°15'14.44" y 11°15'24.16", con las lon- gitudes oeste 75°41'11.60" y 75°41'20.68", a una al- titud de 3480 m s. n. m. Esta zona presenta un clima  templado semiseco con alta humedad durante  todo el año. La temperatura media anual oscila en- tre 6 y 9 °C, con temperaturas máximas anuales que  varían entre 14 y 18 °C. Los meses más cálidos van  de octubre a marzo.

-294-

Scientia Agropecuaria 17(2): 293-303 (2026)                           Cairampoma et al.

Las lluvias acontecen durante todo el año, con un  período de abundancia en los meses de diciembre  a marzo (80-93 mm mensuales) y un período seco  de junio a agosto. Estas condiciones climáticas son  propias de las "yungas" o regiones de bosque nu- boso y son ideales para el cultivo de papa, así como  también para el desarrollo de P. infestans. El área  de estudio presenta una pendiente pronunciada  (~40%); de acuerdo con Ditzler et al. (2017) estas  tierras se clasifican como muy escarpadas. En este  agroecosistema, las áreas de siembra son peque- ñas, con campos de cultivo que tienen una exten- sión promedio de 2,7 mil m².

estas condiciones seleccionamos las parcelas con  cultivos que presentaban síntomas claramente  visibles del tizón tardío en los folíolos. Correspon- diendo a una incidencia de la enfermedad entre el  2 y 3, en la escala del 1 al 9 propuesta por Henfling  (1987). Para garantizar que las lesiones evaluadas  fueran causadas exclusivamente por P. infestans, la  identificación visual fue validada al momento del  etiquetado por expertos fitopatólogos, quienes  confirmaron la presencia de signos característicos  (como la esporulación blanquecina en el envés de  las hojas húmedas) y descartaron síntomas similares  provocados por otros patógenos como Alternaria  solani.

2.2. Detección del tizón tardío en folíolos de papa  Para cumplir con el objetivo propuesto, el presente  estudio sigue tres fases (Figura 2), las cuales se pa- san a describir a continuación.

A2. Toma de fotografías con el dron

Las evaluaciones se llevaron a cabo entre los meses  de enero y marzo. Durante este periodo de evalua- ciones se registraron temperaturas mínimas de 7,9  ºC y máximas de 22,2 ºC, con una humedad relativa  promedio del 83,15% y una acumulación de lluvias  de 289 mm. Estas condiciones agroclimáticas con- tribuyeron de manera significativa al desarrollo de  la rancha en el área de estudio (Ortiz et al., 2004).  Para las evaluaciones de campo se utilizó un dron  del tipo Phantom 4 Pro, provisto con un sensor  CMOS de 1" con una resolución efectiva de  5472×3078 (20 megapíxeles).

A. Procesamiento de datos

A1. Selección de áreas de evaluación  El cultivo de la papa se siembra en la localidad de  Huasahuasi desde septiembre hasta noviembre. Sin  embargo, el día de siembra de cada parcela se rea- liza según el criterio de cada agricultor. Por lo tanto,  durante los meses de evaluación se encontraron  cultivos de papa en distintas fases fenológicas y con  diferentes niveles de incidencia de P. infestans. En

Figura 1. Ubicación de las áreas de estudio.

-295-

Scientia Agropecuaria 17(2): 293-303 (2026)                           Cairampoma et al.

Figura 2. Flujograma para la detección del tizón tardío en folíolos de papa. A) Procesamiento de imágenes obtenidos con dron. B)

Segmentación de instancias de lesiones de tizón tardío (Phytophthora infestans) en folíolos de papa utilizando Mask R-CNN con

backbone ResNet-50 y ResNet-101 y C) aplicación de la red neuronal Mask R-CNN entrenada.

-296-

Scientia Agropecuaria 17(2): 293-303 (2026)                           Cairampoma et al.

Los vuelos se realizaron a una altura de tres metros  sobre el dosel del cultivo, manteniendo la cámara  perpendicular al follaje. Para optimizar la calidad de  las imágenes, las operaciones de vuelo se realiza- ron los días con menor presencia de niebla y pre- ferentemente en ausencia de viento, típicamente  entre las 11:00 a.m. y las 12:30 p.m. En total, se  tomaron 100 fotografías durante todo el periodo de  recolección de datos en campo.

B2. Evaluación del modelo  Para determinar la precisión de los cuadros delimi- tadores predichos por el modelo Mask R-CNN con  relación a la posición correcta de una lesión ocasio- nada por P. Infestans en la foto, el modelo asigna  una clase binaria a cada cuadro delimitador: (1) pro- babilidad de que el cuadro delimitador enmarque  una lesión; y (2) probabilidad de que el cuadro  delimitador enmarque un área sin lesión. La  disyunción entre ambas posibilidades se estableció  mediante el umbral IoU (Intersection over Union). En  el presente trabajo este valor se definió en 0,7  (Ecuación 1). Yan et al. (2019) concluyeron que el  rendimiento de Mask R-CNN es sensible al IoU, es- pecialmente cuando se trata de objetos pequeños  como en nuestro caso. El uso de un umbral de IoU  más alto (p. ej., > 0,8) podría mejorar la precisión,  pero también podría hacer que el modelo pase por  alto algunos casos reales. Por el contrario, elegir un  umbral de IoU más bajo (p. ej., 0,6) podría aumen- tar la cantidad de falsos positivos. En este contexto,  la elección del valor del umbral de IoU en el pre- sente trabajo se justifica debido a la naturaleza irre- gular y a las dimensiones de las lesiones causadas  por P. infestans. El objetivo es garantizar que las  predicciones del modelo no solo detecten adecua- damente los daño, sino que también reflejen con  precisión la extensión real de las lesiones.

A3. Procesamiento de imágenes   Las fotografías se dividieron en cuatro partes, con  el objetivo de optimizar el proceso de entrena- miento y validación de la ANN Mask R-CNN. Las  400 imágenes resultantes de este proceso se some- tieron a un riguroso control de calidad mediante  inspección visual, con la finalidad de eliminar las  que presentaban espacios sin cultivos de papa, con  exceso de maleza, mal enfocadas, fotos pixeladas,  con textura granulada o presencia de halo. Así, se  obtuvieron 200 imágenes RGB de calidad con di- mensiones de 1369×1825 píxeles. De este conjunto  de imágenes, 150 se destinaron al entrenamiento  del modelo y los 50 restantes al proceso de  validación.

B. Entrenamiento y evaluación del modelo

B1. Entrenamiento del modelo  Con la finalidad de identificar las lesiones ocasiona- das por P. infestans en las imágenes, se implementó  la red neuronal convolucional del tipo Mask R-CNN  (Rosebrock, 2017). Esta combina las estructuras de  detección de objetos de última generación Faster  R-CNN propuesta por Ren et al. (2015) y la red neu- ronal convolucional FCN que segmenta imágenes  (Shelhamer et al., 2017). Faster R-CNN proporciona  dos resultados para cada objeto identificado; un re- cuadro delimitador y una etiqueta de clase, mien- tras que FCN indica los píxeles correspondientes a  la lesión identificada.  El entrenamiento y la validación de la red neuronal  se realizaron en un ordenador equipado con una  tarjeta gráfica Nvidia Quadro P1000 y con un pro- cesador Intel Core i9-9900K de novena generación.  Se creó un entorno virtual denominado “Mask R- CNN” desarrollado en Python 3.6. Además, se utili- zaron las librerías de código abierto TensorFlow- gpu V1.5 y Keras V2.1, ambas especializadas en téc- nicas de aprendizaje profundo. En la ejecución de  Mask R-CNN se usaron dos arquitecturas de redes  neuronales profundas; ResNet-50 y ResNet-101. El  algoritmo se implementó utilizando el repositorio  de Matterport Inc., con licencia MIT. Además, para  optimizar el proceso de entrenamiento se utilizó el  modelo preentrenado MS COCO (Abdulla, 2021).

A∪B {> 0,7 →Con P. infestans.

A∩B

IoU =

< 0,3 → Sin P. infestans.    (1)

La relación A ∩B en la Ecuación 1 está determinada  por el área en común entre el cuadro delimitador  predicho por Mask R-CNN y el recuadro que en- marca un área dañada por el tizón tardío. Por su  parte, la relación A ∪B está determinada por la  unión de ambos recuadros. El IoU permite estable- cer los siguientes criterios de identificación: si el IoU  es igual o superior a 0,7, el modelo considera que  el cuadro delimitador predicho por Mask R-CNN ha  ubicado un área con tizón tardío y lo clasifica como  un verdadero positivo. Por otro lado, si la IoU es  menor de 0,3, el modelo considera que la detección  es incorrecta y lo clasifica como falso positivo. Final- mente, en el caso de no cumplir ninguna de las  condiciones anteriores (0,3 < IoU < 0,7), el modelo  considera la detección neutra. Además, se definie- ron las métricas de evaluación del rendimiento. La  métrica de precisión indica la capacidad de la ANN  para detectar con precisión solo los casos relevan- tes y se calcula como la relación entre los verdade- ros positivos y el total de lesiones identificadas. La  métrica de recuperación, también llamada tasa de  verdaderos positivos, evalúa la aptitud de la ANN  para detectar la mayoría de los casos relevantes; se

-297-

Scientia Agropecuaria 17(2): 293-303 (2026)                           Cairampoma et al.

calcula como la relación entre el número de verda- deros positivos detectados y el total de los casos  positivos (Padilla et al., 2020).

de Supresión de No Máximos (Non-Maximum  Suppression), conservando únicamente aquellas  detecciones cuyo índice de confianza superaba el  umbral preestablecido de 0,7 (70%). De este modo,  se descartaron predicciones de baja certeza o falsos  positivos generados por ruido de fondo, tal como  sugieren implementaciones estándar en agricultura  de precisión (Bondre & Patil, 2024; Ren et al., 2017).  Por último, el sistema superpuso las máscaras ge- neradas y las cajas delimitadoras sobre la imagen  original, etiquetando cada lesión con su porcentaje  de probabilidad (ej. "Rancha 0,992"). Esto permitió  cuantificar visualmente la severidad y distribución  espacial de la enfermedad en el folíolo, validando  la utilidad del modelo para el monitoreo fitosanita- rio (Feng et al., 2023).    3. Resultados y discusión

C. Aplicación del modelo  Una vez entrenada y validada la red neuronal, se  procedió a la fase de inferencia o aplicación del  modelo en nuevas imágenes no vistas por el  sistema, simulando el escenario de operación real  en campo para la detección automatizada de P.  infestans. Inicialmente, las nuevas imágenes  capturadas por el dron (imágenes de prueba) se  sometieron al mismo preprocesamiento que las de  entrenamiento, incluyendo la normalización de di- mensiones y ajustes de contraste, garantizando así  que la entrada fuera consistente con los tensores  esperados por la arquitectura ResNet-101.  A continuación, la imagen procesada se introdujo  en la red Mask R-CNN, donde la red troncal  (ResNet-101) extrajo los mapas de características y  la Red de Propuesta de Regiones (RPN) sugirió  áreas candidatas. Posteriormente, las cabeceras de  la red predijeron simultáneamente la caja delimita- dora (bounding box), la clase del objeto (tizón tar- dío) y la máscara de segmentación a nivel de píxel.  Seguidamente, para evitar detecciones redundan- tes sobre una misma lesión, se aplicó el algoritmo

3.1. Etiquetado de imágenes  Las lesiones etiquetadas abarcaron en promedio  600 píxeles, lo que representa el 0,02% del total de  una imagen procesada. Como era de esperar, las  formas de las lesiones encontradas en las imágenes  fueron ovoides, redondas y algunas amorfas. Estas  se enmarcaron con un polígono siguiendo el con- torno de la lesión (Figura 3).

Figura 3. Etiquetado de folíolos con tizón tardío en el programa VIA ejecutado en Google.

-298-

Scientia Agropecuaria 17(2): 293-303 (2026)                           Cairampoma et al.

Este procedimiento se realizó en el programa VIA  de libre disponibilidad, ejecutado en la plataforma  de Google. El número de lesiones etiquetadas en  cada imagen para el entrenamiento fluctuó entre  20 y 30. En consecuencia, al final del proceso de  etiquetado de las 150 imágenes se obtuvieron alre- dedor de 3,7 mil lesiones identificadas. Con el pro- pósito de evitar la disminución de la precisión o el  aumento de los falsos positivos y negativos, se ha  tenido cuidado de enmarcar los píxeles correspon- dientes a la enfermedad, tratando de que ningún  píxel quedara fuera del polígono delimitador y  evitando enmarcar píxeles de áreas sanas.    3.2. Identificación de lesiones

Posteriormente, el algoritmo propone regiones de  interés en función de los cuadros delimitadores. La  red neuronal convolucional clasifica y refina estas  regiones, permitiendo la detección precisa de las  áreas con rancha, generando máscaras de segmen- tación precisas para cada lesión identificada. Por  ejemplo, en la parte central de la Figura 4b se  observa un folíolo con una lesión causada por P.  Infestans. La red neuronal Mask R-CNN lo identifica  con una probabilidad mayor del 80%, asignándole  la etiqueta de rancha. Este procedimiento facilita la  detección de la rancha y permite la delimitación  eficaz de las áreas dañadas dentro de la imagen,  incluso cuando las lesiones podrían ser difícilmente  perceptibles en una inspección visual.   Se usaron los modelos Mask R-CNN con las arqui- tecturas ResNet-50 y ResNet-101 en cultivos de  papa conducidos por agricultores de la localidad de  Huasahuasi. Para ello, se tomaron fotografías con  el dron siguiendo el mismo protocolo establecido  en la toma de fotos para el proceso de entrena- miento y validación de las ANN. La diferencia es  que se escogieron áreas con cultivos que mostra- ron una incidencia de la enfermedad de uno, que  corresponde a la etapa temprana del desarrollo de  P. infestans.  La fotografía utilizada para describir la aplicación  del modelo Mask R-CNN presentaba 15 lesiones  con un tamaño medio de 300 píxeles que no supe- raban la mitad de un folíolo.

La red neuronal Mask R-CNN permite identificar las  lesiones ocasionadas por P. infestans mediante un  conjunto de cuadros delimitadores de diferentes  tamaños que pasan por cada píxel de la imagen,  efectuando un barrido completo. La Figura 4a  muestra una imagen con quince cuadros delimita- dores para un solo píxel. Los rectángulos con una  tonalidad de color similar ostentan tres relaciones  diferentes entre su ancho y su altura (1:1, 1:2 y 2:1).  Existen cinco grupos con diferentes tonalidades y  dimensiones (322, 642, 1282, 2562 y 5122 píxeles).  Estas relaciones y dimensiones de los cuadros deli- mitadores confieren la capacidad de capturar las  formas descritas del tizón tardío en los folíolos de  la papa (Zand et al., 2022).

Figura 4. Proceso de detección de lesiones ocasionadas por P. infestans. a) Cuadros delimitadores definidos para un píxel. b) Folíolo con

lesión. c) Resultado de la identificación de una lesión ocasionada por P. infestans.

-299-

Scientia Agropecuaria 17(2): 293-303 (2026)                           Cairampoma et al.

Figura 5. Resultado de la aplicación del modelo Mask R-CNN con arquitectura ResNet-50.

Por tratarse de un área minúscula, no es fácil ob- servarlas a simple vista; por lo que no podrían de- tectarse en una evaluación de campo. Comparati- vamente, en estudios como el de Lin et al. (2022) se  ha logrado una alta precisión en la detección de  frutas y flores en el cultivo de fresa en condiciones  complejas, en las que el tamaño del objetivo es muy  pequeño en comparación con la foto analizada.  Este reporte refuerza aún más la metodología.  Al aplicar Mask R-CNN con arquitectura ResNet 50  se encontraron tres falsos positivos y trece fueron  verdaderos positivos, además de tres FN en la ima- gen seleccionada (Figura 5). Este resultado  concuerda con la curva de precisión y la tasa de  verdaderos positivos determinados en la etapa de  validación del modelo, lo que indica que, al detec- tar un gran número de lesiones, el número de falsos  positivos también aumenta. En este sentido, pode- mos resaltar que uno de los verdadero positivo es  una hoja seca de eucalipto (Eucalyptus globulus) del  tipo falciforme, a pesar del tamaño de su área y  forma, que difiere notablemente de una lesión

producida por el tizón tardío. En consecuencia, este  modelo no tiene una buena performance en la de- tección de lesiones ocasionadas por P. infestans en  hojas del cultivo de papa.  La Figura 6 muestra la misma imagen, ahora con las  lesiones identificadas aplicando el modelo Mask R- CNN con arquitectura ResNet 101. Este modelo de- tectó once lesiones ocasionadas por P. infestans, en  las que no existe ningún falso positivo y todos son  verdadero positivo. Además, se observó 4 FN. De- bido a su notable precisión al momento de identi- ficar las lesiones ocasionadas por P. infestans en la  imagen de evaluación, con un reducido número de  falsos positivos y falsos negativos, demostrando un  elevado nivel de recuperación, consideramos que  el modelo Mask R-CNN con arquitectura ResNet  101 es superior al modelo con arquitectura ResNet  50.  Al comparar las redes neuronales Mask R-CNN con  las arquitecturas ResNet 50 y ResNet 101, se eviden- ció que ANN basada en ResNet 101 tuvo un mejor  performance que la basada en ResNet 50 al ofrecer

-300-

Scientia Agropecuaria 17(2): 293-303 (2026)                           Cairampoma et al.

un mejor rendimiento a la hora de identificar las le- siones ocasionadas por P. infestans. Esta superiori- dad se debe a que ResNet 101 logra mejor entrena- miento en comparación con la ResNet 50. Esta di- ferencia también se observa en la alta precisión que  logra a medida que aumenta la tasa de verdaderos  positivos. Esta capacidad de capturar una amplia  gama de formas y tamaños de lesiones es crucial  para la detección precisa del tizón tardío, dadas las  características irregulares y variadas de las lesiones.   El resultado de un mejor entrenamiento se refleja  en la performance de la red neuronal para detectar  la mayoría de las lesiones, al tiempo que se reducen  los falsos positivos y los falsos negativos. Esto se co- rrobora con la diferencia en la métrica de precisión  alcanzada en las arquitecturas Resnet 101 (73,5%) y  Resnet 50 (64,5%). Nuestros resultados concuerdan  con los reportados por Hindarto (2023), quien  prueba estas arquitecturas para la detección de en- fermedades de las hojas del maíz. Adicionalmente,  hay que considerar que ResNet-50 suele ofrecer un  mejor rendimiento en aplicaciones prácticas, espe- cialmente cuando el conjunto de datos no es tan

grande o diverso como para beneficiarse de la ma- yor complejidad, por lo que es ideal comparar am- bas arquitecturas. Por ejemplo, Phan et al. (2023)  reportaron que ResNet-50 produjo una precisión  del 98% en la clasificación de tomates en compara- ción con el 97% de ResNet-101.  Recientemente, se han publicado trabajos, como  los de Bondre & Patil (2024) y Feng et al. (2023),  que confirman nuestros resultados y proporcionan  un soporte adicional a nuestros hallazgos, lo que  nos permite proponer la red neuronal Mask R-CNN  con arquitectura ResNet 101 como un método fiable  para la detección de lesiones ocasionadas por P.  Infestans en el cultivo de papa. Sin embargo, a di- ferencia de estos estudios nuestro planteamiento  de usar drones para la evaluación en campo mues- tra la innovación de nuestro método para superar  las complejidades inherentes de la zona de estudio  con terrenos irregulares y vegetación densa que a  menudo obstaculizan los métodos de evaluación  tradicionales. Para ello, aprovechamos el poder de  las tecnologías emergentes de agricultura de preci- sión.

Figura 6. Resultado de la aplicación del modelo Mask R-CNN con arquitectura ResNet-101.

-301-

Scientia Agropecuaria 17(2): 293-303 (2026)                           Cairampoma et al.

El uso de imágenes capturadas con drones nos  permitió superar los límites de lo que es posible  para la detección de enfermedades de manera au- tomatizada y escalable. Por tanto, los desafíos que  imponen estos agroecosistemas con alta incidencia  de P. infestans y de difícil acceso requieren el desa- rrollo de enfoques innovadores para el monitoreo  y manejo del tizón tardío. De acuerdo con Grados  et al. (2020), existe una oportunidad significativa  para mejorar los rendimientos del cultivo de papa  en zonas altoandinas mediante un uso más racional  de insumos y mejores prácticas agrícolas. Teniendo  en cuenta que el cultivo de papa debe abordar las  cargas ambientales dentro de las limitaciones so- cioeconómicas locales. Al proponer una herra- mienta automatizada y precisa para la detección  temprana del tizón tardío, nuestra propuesta puede  contribuir a mejorar la productividad del cultivo de  papa, al tiempo que facilita prácticas de manejo  más racionales y sostenibles, como la aplicación  controlada de pesticidas, de acuerdo con las reco- mendaciones de Babli et al. (2022). Esta integración  de innovaciones tecnológicas y enfoques de inten- sificación sostenible es crucial para potenciar el  desarrollo del sector papero en estos entornos  desafiantes de las zonas altoandinas.    4. Conclusiones

dron para la recopilación de imágenes representa  una ventaja clave de nuestro método. Esta pro- puesta de captura de datos permite superar las li- mitaciones inherentes a los entornos agrestes y de  alta pendiente, donde los métodos de inspección  manual a menudo son ineficientes e impracticables.  La capacidad de identificar lesiones es particular- mente notable, ya que proporciona información  detallada sobre el alcance y la distribución de los  síntomas de la enfermedad, lo cual es crucial para  implementar  intervenciones  oportunas  y  específicas.  Finalmente, como proyecciones futuras, se reco- mienda la implementación de estos algoritmos en  plataformas de edge computing integradas a los  drones para permitir la toma de decisiones en  tiempo real. Asimismo, sería valioso expandir el en- trenamiento del modelo incorporando diversas va- riedades de papa nativa y condiciones de ilumina- ción variables, así como explorar la fusión de imá- genes RGB con sensores multiespectrales. Esto no  solo refinaría la precisión diagnóstica, sino que sen- taría las bases para sistemas de aplicación automa- tizada de agroquímicos (drones pulverizadores),  optimizando recursos y reduciendo el impacto am- biental en los Andes.    Agradecimientos  Los autores del proyecto de investigación agradecen a la  Universidad Nacional del Centro del Perú (UNCP) por su  financiamiento a través de la IV Convocatoria para el  financiamiento de Proyectos de Investigación con fondos canon,  sobre canon y regalías mineras.     Conflictos de interés: los autores declaran no tener conflictos de  interés.    Contribución de los autores  J.A. Cairampoma: Supervisión, Administración del proyecto,  Obtención de fondos, Metodología, Programación. Delia  Gamarra-Gamarra: Metodología, Investigación, Redacción –  revisión y edición. F.E. Dionisio: Asistente, Procesamiento de datos,  Metodología, Investigación.    ORCID

El uso del dron Phantom 4 Pro, combinado con re- des neuronales profundas como Mask R-CNN, ha  demostrado ser una técnica promisoria en la eva- luación de la incidencia del tizón tardío en los folío- los de papa en campos de agricultores de Hua- sahuasi (3480 m s. n. m.). El modelo basado en la  arquitectura ResNet 101 alcanzó una precisión del  73,5% con un IoU del 70%, lo que le permitió iden- tificar lesiones de aproximadamente 400 píxeles en  imágenes RGB de 2,4 megapíxeles.  Al comparar las arquitecturas ResNet50 y Res- Net101, se concluye que ResNet101 generalmente  ofrece una precisión ligeramente superior para la  identificación del tizón tardío en cultivos de papa.  Aunque requiere más recursos computacionales y  tiempo de procesamiento en comparación con las  50 capas de ResNet50, el incremento marginal en  el rendimiento justifica su aplicación, especialmente  si el tamaño del conjunto de datos es el adecuado.   En general, la aplicación de técnicas avanzadas de  visión por computadora se ha convertido en un en- foque prometedor para la detección y el segui- miento de enfermedades en el cultivo de papa.  Aquí hemos resaltado la ventaja que ofrece esta  metodología sobre los métodos tradicionales de  evaluación y diagnóstico. En particular, el uso del

J. A. Cairampoma   https://orcid.org/0000-0002-1998-6178  D. Gamarra-Gamarra   https://orcid.org/0000-0002-6262-237X   F. E. Dionisio   https://orcid.org/0000-0002-9769-6782     Referencias bibliográficas

Abbas, A., Zhang, Z., Zheng, H., Alami, M. M., Alrefaei, A. F., Abbas, Q.,

Naqvi, S. A. H., Rao, M. J., Mosa, W. F. A., & Abbas, Q. (2023).  Drones in plant disease assessment, efficient monitoring, and  detection: a way forward to smart agriculture. Agronomy, 13(6),  1524. https://doi.org/10.3390/agronomy13061524  Abdulla, W. (2021). Mask R-CNN for object detection and instance

segmentation  on  Keras  and  TensorFlow.  https://github.com/matterport/Mask_RCNN  Alanazi, R. (2025). A YOLOv10-based Approach for Banana Leaf

Disease Detection. Engineering, Technology & Applied Science  Research,  15(3),  23522-23526.  https://doi.org/10.48084/etasr.11138

-302-

Scientia Agropecuaria 17(2): 293-303 (2026)                           Cairampoma et al.

Baba, A. (2024). Neural networks from biological to artificial and vice

Science  and  Technology,  5(3),  261-266.  https://doi.org/10.24925/turjaf.v5i3.261-266.1038  Matsuo, Y., LeCun, Y., Sahani, M., Precup, D., Silver, D., Sugiyama, M.,

versa.  Biosystems,  235,  105110.  https://doi.org/https://doi.org/10.1016/j.biosystems.2023.105110  Babli, D., Yadav, P. S., & Sheeren Parveen, V. K. (2022). Efficacy of

Uchibe, E., & Morimoto, J. (2022). Deep learning, reinforcement  learning, and world models. Neural Networks, 152, 267-275.  https://doi.org/https://doi.org/10.1016/j.neunet.2022.03.037  MK, D., & Matharasi, P. B. (2025). Leaf Disease Predictions Using Deep

different eco-friendly methods against late blight of potato,  Phytophthora infestans: A review. Pharma Innov. J, 11, 1949-1961.  Bai, X., Wang, X., Liu, X., Liu, Q., Song, J., Sebe, N., & Kim, B. (2021).

Explainable deep learning for efficient and robust pattern  recognition: A survey of recent developments. Pattern  Recognition,  120,  108102.  https://doi.org/https://doi.org/10.1016/j.patcog.2021.108102  Berhan, M. (2021). Review on epidemiology, sampling techniques,

Learning Techniques - Potato. International Journal of Information  Technology,  Research  and  Applications,  4(3),  33-42.  https://doi.org/10.59461/ijitra.v4i3.166  Ortiz, O., Garrett, K. A., Health, J. J., Orrego, R., & Nelson, R. J. (2004).

Management of potato late blight in the Peruvian highlands:  evaluating the benefits of farmer field schools and farmer  participatory  research.  Plant  Disease,  88(5),  565-571.  https://doi.org/10.1094/PDIS.2004.88.5.565  Padilla, R., Netto, S. L., & da Silva, E. A. B. (2020). A Survey on

management strategies of late blight (Phytophthora infestans) of  potato and its yield loss. Asian Journal of Advances in Research,  4(1), 199-207. https://doi.org/10.1007/978-3-030-28683-5_1  Bondre, S., y Patil, D. (2024). Crop disease identification segmentation

algorithm based on Mask-RCNN. Agronomy Journal, 116(3), 1088- 1098. https://doi.org/https://doi.org/10.1002/agj2.21387  Devaux, A., Goffart, J.-P., Petsakos, A., Kromann, P., Gatto, M., Okello,

Performance Metrics for Object-Detection Algorithms. 2020  International Conference on Systems, Signals and Image  Processing  (IWSSIP),  237-242.  https://doi.org/10.1109/IWSSIP48289.2020.9145130  Perez, W., Forbes, G. A., Arias, R., Pradel, W., Kawarazuka, N., &

J., Suarez, V., & Hareau, G. (2020). Global food security,  contributions from sustainable potato agri-food systems. The  potato crop: Its agricultural, nutritional and social contribution to  humankind, 3-35. https://doi.org/10.1007/978-3-030-28683-5_1  Ditzler, C., Scheffe, K., & Monger, H. C. (2017). Soil survey manual. USDA

Andrade-Piedra, J. (2022). Farmer Perceptions Related to Potato  Production and Late Blight Management in Two Communities in  the Peruvian Andes. Frontiers in Sustainable Food Systems, 6,  873490. https://doi.org/10.3389/fsufs.2022.873490  Phan, Q.-H., Nguyen, V.-T., Lien, C.-H., Duong, T.-P., Hou, M. T.-K., &

Handbook 18. Government Printing Office.  Duarte-Carvajalino, J., Alzate, D., Ramirez, A., Santa-Sepulveda, J.,

Fajardo-Rojas, A., Soto-Suárez, M., Duarte-Carvajalino, J. M.,  Alzate, D. F., Ramirez, A. A., Santa-Sepulveda, J. D., Fajardo-Rojas,  A. E., & Soto-Suárez, M. (2018). Evaluating Late Blight Severity in  Potato Crops Using Unmanned Aerial Vehicles and Machine  Learning  Algorithms.  Remote  Sensing,  10(10),  1513.  https://doi.org/10.3390/rs10101513  Feng, J., Hou, B., Yu, C., Yang, H., Wang, C., Shi, X., & Hu, Y. (2023).

Le, N.-B. (2023). Classification of tomato fruit using yolov5 and  convolutional neural network models. Plants, 12(4), 790.  https://doi.org/10.3390/plants12040790  Ren, S., He, K., Girshick, R., & Sun, J. (2016). Faster R-CNN: Towards real-

time object detection with region proposal networks. IEEE  transactions on pattern analysis and machine intelligence, 39(6),  1137–1149. https://doi.org/10.1109/TPAMI.2016.2577031  Rosebrock, A. (2017). Deep Learning for Computer Vision with Python:

Research and Validation of Potato Late Blight Detection Method  Based  on  Deep  Learning.  Agronomy,  13(6),  1659.  https://doi.org/10.3390/agronomy13061659  Ganesh, P., Volle, K., Burks, T. F., & Mehta, S. S. (2019). Deep Orange:

ImageNet Bundle. PyImageSearch.  Shelhamer, E., Long, J., & Darrell, T. (2017). Fully convolutional networks

for semantic segmentation. IEEE transactions on pattern analysis  and machine intelligence, 39(4), 640-651.  Sinamenye, J. H., Chatterjee, A., & Shrestha, R. (2025). Potato plant

Mask R-CNN based Orange Detection and Segmentation. IFAC- PapersOnLine,  52(30),  70-75.  https://doi.org/10.1016/j.ifacol.2019.12.499  Grados, D., García, S., & Schrevens, E. (2020). Assessing the potato yield

disease detection: leveraging hybrid deep learning models. BMC  Plant Biology, 25(1), 647. https://doi.org/10.1186/s12870-025- 06679-4  Wang, F., Wang, C., Song, S., Xie, S., & Kang, F. (2021). Study on starch

gap in the Peruvian Central Andes. Agricultural Systems, 181,  102817. https://doi.org/https://doi.org/10.1016/j.agsy.2020.102817  Hindarto, D. (2023). Comparison of Detection with Transfer Learning

content detection and visualization of potato based on  hyperspectral imaging. Food Science & Nutrition, 9(8), 4420-4430.  https://doi.org/https://doi.org/10.1002/fsn3.2415  Yan, J., Wang, H., Yan, M., Diao, W., Sun, X., & Li, H. (2019). IoU-Adaptive


## Architecture RestNet18, RestNet50, RestNet101 on Corn Leaf

Disease. Jurnal Teknologi Informasi Universitas Lambung 
Mangkurat 
(JTIULM), 
8(2), 
41-48. 
https://doi.org/10.20527/jtiulm.v8i2.174 
Ivanov, A. A., Ukladov, E. O., & Golubeva, T. S. (2021). Phytophthora

Deformable R-CNN: Make Full Use of IoU for Multi-Class Object  Detection in Remote Sensing Imagery. Remote Sensing, 11(3).  https://doi.org/10.3390/rs11030286  Yu, M., Ma, X., Guan, H., Liu, M., & Zhang, T. (2022). A Recognition

infestans: An Overview of Methods and Attempts to Combat Late  Blight.  Journal  of  Fungi,  7(12),  1071.  https://doi.org/10.3390/jof7121071  Jadhav, P., Kachave, V., Mane, A., & Joshi, K. (2023). Crop detection

Method of Soybean Leaf Diseases Based on an Improved Deep  Learning  Model.  Frontiers  in  Plant  Science,  13.  https://doi.org/10.3389/fpls.2022.878834  Yu, Y., Zhang, K., Yang, L., & Zhang, D. (2019). Fruit detection for

using satellite image processing. I-Manager’s Journal on Image  Processing, 10(2), 50-60. https://doi.org/10.26634/jip.10.2.19800  Kunduracioglu, I., & Pacal, I. (2024). Advancements in deep learning for

strawberry harvesting robot in non-structural environment based  on Mask-RCNN. Computers and Electronics in Agriculture, 163,  104846. https://doi.org/10.1016/j.compag.2019.06.001  Zand, M., Etemad, A., y Greenspan, M. (2022). Objectbox: From centers

accurate classification of grape leaves and diagnosis of grape  diseases. Journal of Plant Diseases and Protection, 131(3), 1061- 1080. https://doi.org/10.1007/s41348-024-00896-z  Lin, P., Zhang, H., Zhao, F., Wang, X., Liu, H., & Chen, Y. (2022). Boosted

to boxes for anchor-free object detection. European Conference  on Computer Vision, 390-406.  Zevallos, E., Inga, J., Alvarez, F., Marmolejo, K., Paitan, R., Viza, I.,

Mask R-CNN algorithm for accurately detecting strawberry plant  canopies in the fields from low-altitude drone images. Food  Science  and  Technology,  42,  e95922.  https://doi.org/10.1590/fst.95922  Majeed, A., Muhammad, Z., Ullah, Z., Ullah, R., & Ahmad, H. (2017). Late

Becerra, D., Rixi, G., & Silva-Diaz, C. (2021). First signs of late  blight resistance in traditional native potatoes of Pasco—Peru, a  preliminary assay. Agriculture & Food Security, 10(1), 33.  https://doi.org/10.1186/s40066-021-00330-9

blight of potato (Phytophthora infestans) I: Fungicides application  and associated challenges. Turkish Journal of Agriculture-Food

-303-
