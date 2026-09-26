"""Biblioteca de hooks y CTAs por rubro.

Aquí vive la experiencia en redes de Clarea. Para agregar un rubro nuevo,
copia uno existente, cambia sus palabras clave y escribe sus hooks y CTAs.
Cada texto puede usar {brand} para el nombre de la marca.

Los tipos (HOOK_TYPES / CTA_TYPES) explican QUÉ es cada fórmula y POR QUÉ
funciona: es la parte que enseña al emprendedor, no solo le da el texto.
"""

HOOK_DEFINITION = (
    "Un hook (gancho) es la primera frase de tu publicación o los primeros 3 segundos "
    "de tu video. Su único trabajo es que la persona deje de deslizar y se quede a mirar."
)

CTA_DEFINITION = (
    "Un CTA (llamado a la acción) es la instrucción final que le dice a la persona "
    "exactamente qué hacer ahora. Si no le pides nada, no hará nada."
)

HOOK_TYPES = {
    "pregunta": {
        "nombre": "Pregunta de deseo",
        "por_que": "Hace que la persona se imagine con el resultado; si se lo imagina, sigue leyendo.",
    },
    "error": {
        "nombre": "Error común",
        "por_que": "A nadie le gusta equivocarse con su dinero; el miedo a perder atrapa más que la promesa de ganar.",
    },
    "antes_despues": {
        "nombre": "Antes y después",
        "por_que": "Muestra la transformación real; es prueba social y genera credibilidad inmediata.",
    },
    "costo": {
        "nombre": "Costo real",
        "por_que": "El precio es la duda número uno; hablarlo abiertamente genera confianza y filtra curiosos.",
    },
    "detras_escena": {
        "nombre": "Detrás de escena",
        "por_que": "Enseñar el proceso humaniza la marca y demuestra que sabes lo que haces.",
    },
}

CTA_TYPES = {
    "palabra_clave": {
        "nombre": "Palabra clave por mensaje",
        "por_que": "Fricción cero: escribir una palabra es fácil, y cada mensaje es un cliente potencial medible.",
    },
    "whatsapp": {
        "nombre": "WhatsApp directo",
        "por_que": "Lleva la conversación al canal donde se cierra la venta, sin pasos intermedios.",
    },
    "agenda": {
        "nombre": "Agendar",
        "por_que": "Convierte el interés en un compromiso con fecha; quien agenda ya está decidido.",
    },
    "comentario": {
        "nombre": "Comentar",
        "por_que": "Cada comentario le dice al algoritmo que el contenido vale la pena y le da más alcance.",
    },
    "recurso": {
        "nombre": "Recurso gratis",
        "por_que": "Das valor antes de vender; quien pide la guía ya está investigando y es un cliente calificado.",
    },
}

INDUSTRIES = {
    "piscinas": {
        "nombre": "Piscinas y construcción",
        "keywords": ["piscina", "pileta", "jacuzzi", "construc", "obra", "remodel"],
        "hooks": {
            "pregunta": "¿Cuánto cambia una casa cuando le agregas una piscina?",
            "error": "3 errores que encarecen tu piscina antes de poner el primer ladrillo.",
            "antes_despues": "Así era este patio hace 60 días. Así se ve hoy.",
            "costo": "¿Cuánto cuesta realmente una piscina? Te lo contamos sin letra chica.",
            "detras_escena": "Así construye {brand} una piscina, paso a paso.",
        },
        "ctas": {
            "palabra_clave": "Escríbenos 'PISCINA' por mensaje y te enviamos una cotización referencial.",
            "whatsapp": "Escríbenos por WhatsApp y habla directo con el ingeniero a cargo.",
            "agenda": "Agenda una visita técnica sin costo a tu casa.",
            "comentario": "Comenta '¿techada o al aire libre?' y te contamos cuál conviene más.",
            "recurso": "Pide nuestra guía gratis: 'Todo lo que debes saber antes de construir tu piscina'.",
        },
    },
    "restaurante": {
        "nombre": "Restaurantes y comida",
        "keywords": ["restaurante", "comida", "menu", "menú", "cafe", "café", "pizza", "sushi",
                     "cocina", "postre", "pasteler", "panader", "delivery", "hamburgues"],
        "hooks": {
            "pregunta": "¿Cuándo fue la última vez que una comida te hizo cerrar los ojos?",
            "error": "El error que cometen casi todos al pedir en {brand} (y cómo evitarlo).",
            "antes_despues": "De ingredientes frescos a tu mesa en 15 minutos. Míralo.",
            "costo": "Almorzar rico por menos de lo que imaginas: te mostramos cómo.",
            "detras_escena": "Esto es lo que pasa en nuestra cocina antes de que abramos.",
        },
        "ctas": {
            "palabra_clave": "Escríbenos 'MENU' y te enviamos la carta de hoy.",
            "whatsapp": "Haz tu pedido directo por WhatsApp, sin apps ni comisiones.",
            "agenda": "Reserva tu mesa para este fin de semana antes de que se llene.",
            "comentario": "Etiqueta a la persona con la que vendrías a probar esto.",
            "recurso": "Pide nuestro menú de la semana y elige con tiempo.",
        },
    },
    "belleza": {
        "nombre": "Belleza y estética",
        "keywords": ["belleza", "estetica", "estética", "spa", "salon", "salón", "uñas", "peluquer",
                     "barber", "maquillaje", "facial", "depilac", "pestañas", "cejas"],
        "hooks": {
            "pregunta": "¿Y si tu rutina de cuidado te tomara la mitad del tiempo?",
            "error": "3 errores que arruinan tu tratamiento en casa sin que lo notes.",
            "antes_despues": "Una sola sesión. Mira la diferencia.",
            "costo": "¿Vale la pena pagar por un tratamiento profesional? Hagamos las cuentas.",
            "detras_escena": "Así preparamos cada cita en {brand} para que salgas feliz.",
        },
        "ctas": {
            "palabra_clave": "Escríbenos 'CITA' y te mostramos los horarios libres de esta semana.",
            "whatsapp": "Agenda por WhatsApp en menos de un minuto.",
            "agenda": "Reserva tu cita hoy: los cupos del sábado vuelan.",
            "comentario": "Comenta qué te gustaría cambiar y te recomendamos el tratamiento ideal.",
            "recurso": "Pide gratis nuestra rutina de cuidado para tu tipo de piel.",
        },
    },
    "inmobiliaria": {
        "nombre": "Inmobiliarias",
        "keywords": ["inmobiliari", "departamento", "depa", "propiedad", "terreno", "alquiler",
                     "arriendo", "bienes raices", "bienes raíces", "condominio"],
        "hooks": {
            "pregunta": "¿Y si en vez de pagar alquiler, esa cuota fuera para tu propio departamento?",
            "error": "El error más caro al comprar tu primer departamento.",
            "antes_despues": "Así se veía en planos. Así se ve con la familia viviendo.",
            "costo": "¿Cuánto necesitas realmente para la cuota inicial? Te lo explicamos.",
            "detras_escena": "Recorre con nosotros este departamento antes que nadie.",
        },
        "ctas": {
            "palabra_clave": "Escríbenos 'VISITA' y coordinamos un recorrido esta semana.",
            "whatsapp": "Escríbenos por WhatsApp y te enviamos planos y precios.",
            "agenda": "Agenda tu visita al piloto este fin de semana.",
            "comentario": "Comenta '¿comprar o alquilar?' y te damos nuestra opinión honesta.",
            "recurso": "Pide gratis nuestra guía para comprar tu primer departamento.",
        },
    },
    "retail": {
        "nombre": "Tiendas y productos",
        "keywords": ["tienda", "store", "ropa", "moda", "zapatill", "accesorio", "boutique",
                     "producto", "catalogo", "catálogo", "juguete", "joya"],
        "hooks": {
            "pregunta": "¿Buscabas algo que combine con todo? Lo encontraste.",
            "error": "3 errores al comprar online que te hacen gastar de más.",
            "antes_despues": "Mismo look, un solo cambio. Mira la diferencia.",
            "costo": "Calidad de tienda grande, precio de tienda de barrio.",
            "detras_escena": "Así elegimos cada producto que llega a {brand}.",
        },
        "ctas": {
            "palabra_clave": "Escríbenos 'QUIERO' y te separamos el tuyo.",
            "whatsapp": "Pide el tuyo por WhatsApp y te lo enviamos a casa.",
            "agenda": "Aparta el tuyo hoy: quedan pocas unidades.",
            "comentario": "Comenta tu favorito: ¿el 1, el 2 o el 3?",
            "recurso": "Pide nuestro catálogo completo con precios.",
        },
    },
    "servicios": {
        "nombre": "Servicios profesionales",
        "keywords": ["consultor", "asesor", "abogad", "contador", "contable", "agencia", "marketing",
                     "legal", "coach", "capacitac", "servicio"],
        "hooks": {
            "pregunta": "¿Cuántas horas a la semana pierdes en algo que otro podría resolver por ti?",
            "error": "El error que le cuesta dinero a la mayoría de negocios pequeños.",
            "antes_despues": "Así llegó este cliente. Así está hoy.",
            "costo": "¿Cuánto cuesta NO contratar a un profesional? Hagamos las cuentas.",
            "detras_escena": "Así trabajamos en {brand} con cada cliente, desde el primer día.",
        },
        "ctas": {
            "palabra_clave": "Escríbenos 'ASESORIA' y te contamos cómo podemos ayudarte.",
            "whatsapp": "Escríbenos por WhatsApp y resolvemos tu duda hoy.",
            "agenda": "Agenda una llamada gratis de 15 minutos.",
            "comentario": "Comenta tu mayor duda y la respondemos en el próximo post.",
            "recurso": "Pide gratis nuestro checklist para empezar con buen pie.",
        },
    },
    "general": {
        "nombre": "General",
        "keywords": [],
        "hooks": {
            "pregunta": "¿Qué cambiaría en tu día si tuvieras esto resuelto?",
            "error": "3 errores que cometen casi todos antes de comprar (y cómo evitarlos).",
            "antes_despues": "Así estaba antes. Así quedó con {brand}.",
            "costo": "¿Cuánto cuesta realmente? Te lo contamos sin rodeos.",
            "detras_escena": "Esto es lo que no ves detrás de cada pedido de {brand}.",
        },
        "ctas": {
            "palabra_clave": "Escríbenos 'INFO' por mensaje y te respondemos hoy.",
            "whatsapp": "Escríbenos por WhatsApp para atenderte al instante.",
            "agenda": "Agenda tu cita o pedido hoy mismo.",
            "comentario": "Comenta 'QUIERO' y te enviamos los detalles.",
            "recurso": "Pide gratis nuestra guía con todo lo que necesitas saber.",
        },
    },
}
