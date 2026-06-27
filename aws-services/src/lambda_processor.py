import os
import json
import base64
from pydantic import BaseModel
from typing import Optional
from services.api import execute_get_request

FASTAPI_URL = os.environ.get("BACKEND_API_URL", "http://host.docker.internal:8000")

class BoundingBox(BaseModel):
    Width: float
    Height: float
    Left: float
    Top: float


class PersonInstance(BaseModel):
    BoundingBox: BoundingBox
    Confidence: float


class RekognitionPayload(BaseModel):
    PersonDetected: bool = False
    PersonInstance: Optional[PersonInstance] = None


def lambda_handler(event, context):
    print("=== Lambda Procesando Evento de Kinesis ===")
    endpoint = f"{FASTAPI_URL}/move"

    for record in event["Records"]:
        try:
            payload_encoded = record["kinesis"]["data"]
            payload_decoded = base64.b64decode(payload_encoded).decode("utf-8")

            data = json.loads(payload_decoded)
            print(f"Payload decodificado: {json.dumps(data, indent=2)}")

            frame_offset = (
                data.get("InputInformation", {})
                .get("KinesisVideoStream", {})
                .get("FrameOffsetInMs", 0)
            )
            persons = data.get("Persons", [])

            print(
                f"\n[PROCESANDO FRAME] Timestamp: {frame_offset}ms | Detectados: {len(persons)}"
            )

            for person in persons:
                track_id = person.get("TrackId")
                confidence = person.get("Person", {}).get("Confidence", 0)
                bbox = person.get("Person", {}).get("BoundingBox", {})

                if confidence < 70:
                    continue

                posicion_x = bbox.get("Left", 0.5) + (bbox.get("Width", 0) / 2)
                posicion_y = bbox.get("Top", 0.5) + (bbox.get("Height", 0) / 2)

                print(
                    f" Centro de Persona ID {track_id} -> X: {round(posicion_x, 2)} | Y: {round(posicion_y, 2)}"
                )

                movements = []

                if posicion_x < 0.20:
                    movements.append("left")
                elif posicion_x > 0.80:
                    movements.append("right")

                if posicion_y < 0.20:
                    movements.append("up")
                elif posicion_y > 0.80:
                    movements.append("down")

                if not movements:
                    print(
                        f"Persona ID {track_id} está DENTRO de la zona segura. No se requiere movimiento."
                    )
                else:
                    for direction in movements:
                        params = {"direction": direction, "time_sec": 0.1}
                        print(
                            f"Centro descentrado. Disparando {direction} para reencuadrar..."
                        )

                        resultado = execute_get_request(endpoint, params)
                        if resultado:
                            print(f"Backend respondió: {resultado}")

        except Exception as e:
            print(f"Error crítico procesando registro dentro del loop: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps("Procesamiento completado con éxito"),
    }
