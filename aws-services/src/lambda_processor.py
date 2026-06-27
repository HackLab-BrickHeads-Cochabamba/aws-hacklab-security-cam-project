import json
import base64
import httpx
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


# --- 1. CONFIGURACIÓN DE ENTORNO ---
class LambdaSettings(BaseSettings):
    FASTAPI_URL: str = "http://127.0.0.1:8000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = LambdaSettings()


# --- 2. MODELOS DE VALIDACIÓN PARA REKOGNITION (PYDANTIC) ---
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
    PersonInstance: PersonInstance | None = None


# --- 3. LÓGICA DE LA LAMBDA ---
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

            # Extraemos coordenadas de posición
            posicion_x = data.PersonInstance.BoundingBox.Left
            posicion_y = data.PersonInstance.BoundingBox.Top
            print(
                f"Persona detectada en X (Left): {posicion_x} | Y (Top): {posicion_y}"
            )

            # Lista de movimientos requeridos para este frame
            movements = []

            # 🛠️ EVALUACIÓN DEL EJE HORIZONTAL (X)
            if posicion_x < 0.35:
                movements.append("left")
            elif posicion_x > 0.65:
                movements.append("right")

            # 🛠️ EVALUACIÓN DEL EJE VERTICAL (Y)
            # Nota: 0.0 es Arriba, 1.0 es Abajo en el plano de AWS Rekognition
            if posicion_y < 0.35:
                movements.append("up")
            elif posicion_y > 0.65:
                movements.append("down")

            # Si la persona está perfectamente encuadrada
            if not movements:
                print(
                    "La persona está centrada en ambos ejes. No se requiere movimiento."
                )
                continue

            # Ejecutar las llamadas correspondientes a tu FastAPI
            endpoint = f"{settings.FASTAPI_URL}/move"

            async_client = (
                httpx.Client()
            )  # Cliente síncrono para entorno Lambda clásico
            with async_client as client:
                for direction in movements:
                    # Ajustamos a ráfagas cortas de 0.1s para evitar movimientos bruscos
                    params = {"direction": direction, "time_sec": 0.1}

                    print(f"Disparando: {endpoint}?direction={direction}&time_sec=0.1")

                    response = client.get(endpoint, params=params, timeout=3.0)
                    response.raise_for_status()
                    print(f"Respuesta de FastAPI para {direction}: {response.json()}")

        except Exception as e:
            print(f"Error procesando el registro: {e}")
