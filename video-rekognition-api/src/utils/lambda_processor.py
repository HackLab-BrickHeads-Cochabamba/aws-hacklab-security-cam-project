import base64
import json
import httpx
from src.config import settings
from pydantic import BaseModel


class BoundingBox(BaseModel):
    Width: float
    Height: float
    Left: float
    Top: float


class PersonInstance(BaseModel):
    # Estructura típica de AWS Rekognition para una instancia detectada
    BoundingBox: BoundingBox
    Confidence: float


class RekognitionPayload(BaseModel):
    # Estructura del JSON que tú envías o que genera Rekognition
    PersonDetected: bool = False
    PersonInstance: PersonInstance | None = None


def lambda_handler(event, context):
    print("=== Lambda Procesando Evento de Kinesis ===")

    for record in event.get("Records", []):
        try:
            # Decodificar el registro de Kinesis
            payload_bytes = base64.b64decode(record["kinesis"]["data"])
            payload_json = json.loads(payload_bytes.decode("utf-8"))

            # Validar los datos de entrada con Pydantic
            data = RekognitionPayload(**payload_json)

            if not data.PersonDetected or not data.PersonInstance:
                print("No se detectó ninguna persona en este registro.")
                continue

            # Extraemos la posición horizontal (Left)
            posicion_x = data.PersonInstance.BoundingBox.Left
            print(f"Persona detectada en la posición X (Left): {posicion_x}")

            # Determinamos la dirección según dónde aparece en pantalla
            direction = None
            if posicion_x < 0.35:
                # Está muy a la izquierda de la pantalla -> Mover a la izquierda para encuadrar
                direction = "left"
            elif posicion_x > 0.65:
                # Está muy a la derecha de la pantalla -> Mover a la derecha para encuadrar
                direction = "right"
            else:
                print("La persona está centrada. No es necesario mover la cámara.")
                continue

            # Ejecutar la petición HTTP a tu FastAPI
            if direction:
                endpoint = f"{settings.FASTAPI_URL}/move"
                params = {
                    "direction": direction,
                    "time_sec": 0.3,
                }  # 300ms de movimiento ligero

                print(
                    f"Enviando comando a FastAPI: {direction.upper()} por {params['time_sec']}s"
                )

                # Petición síncrona (estándar dentro de AWS Lambda tradicional)
                response = httpx.get(endpoint, params=params, timeout=3.0)
                response.raise_for_status()
                print(f"Cámara movida exitosamente. Respuesta: {response.json()}")

        except Exception as e:
            print(f"Error procesando el registro: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps("Procesamiento de Kinesis completado con éxito"),
    }
