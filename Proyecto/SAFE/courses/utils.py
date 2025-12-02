from typing import List, Dict, Any, Optional


def _to_json_safe(value):
    """
    Convierte estructuras anidadas (listas, diccionarios, sets) a una forma
    segura para JSONField (los sets se transforman en listas).
    """
    if isinstance(value, set):
        return [_to_json_safe(v) for v in value]
    if isinstance(value, list):
        return [_to_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_json_safe(v) for k, v in value.items()}
    return value


def parse_evaluacion(texto: str) -> List[Dict[str, Any]]:
    """Parsea preguntas tipo 'Q:' y opciones 'O:' desde un texto."""
    preguntas: List[Dict[str, Any]] = []
    pregunta_actual: Optional[Dict[str, Any]] = None

    for line in texto.splitlines():
        line = line.strip()
        if not line:
            # Línea vacía: separador entre preguntas
            continue

        if line.startswith("Q:"):
            # Guardar pregunta anterior, si había
            if pregunta_actual is not None:
                preguntas.append(pregunta_actual)

            _, resto = line.split("Q:", 1)
            qid, texto_preg = resto.split("|", 1)

            pregunta_actual = {
                "id": qid.strip(),
                "texto": texto_preg.strip(),
                "opciones": [],
            }

        elif line.startswith("O:"):
            if pregunta_actual is None:
                raise ValueError("Opción sin pregunta previa")

            _, resto = line.split("O:", 1)
            oid, texto_opt, flag = resto.split("|", 2)

            es_correcta = flag.strip() == "1"

            pregunta_actual["opciones"].append(
                {
                    "id": oid.strip(),
                    "texto": texto_opt.strip(),
                    "es_correcta": es_correcta,
                }
            )

        else:
            raise ValueError(f"Línea con formato inválido: {line}")

    # Agregar la última pregunta si existe
    if pregunta_actual is not None:
        preguntas.append(pregunta_actual)

    # Validación extra: cada pregunta con al menos una correcta
    for p in preguntas:
        if not any(o["es_correcta"] for o in p["opciones"]):
            raise ValueError(f"La pregunta '{p['id']}' no tiene opción correcta")

    return preguntas


def is_txt_file(uploaded_file) -> bool:
    """
    Verifica si el archivo subido corresponde a un .txt
    usando la extensión del nombre del archivo.
    """
    if not hasattr(uploaded_file, "name"):
        return False
    return uploaded_file.name.lower().endswith(".txt")
