import cv2
import json
import boto3
import os
from mock_rekognition import generate_rekognition_payload

# CONFIGURACIÓN
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(BASE_DIR, "assets", "random.png")
STREAM_NAME = "rekognition-person-stream"

# Conectar a LocalStack
kinesis_client = boto3.client(
    "kinesis",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="mock",
    aws_secret_access_key="mock",
)


def main():
    if not os.path.exists(IMAGE_PATH):
        print(
            f"❌ Error: No encontré la imagen '{IMAGE_PATH}' en la raíz del proyecto."
        )
        print("Por favor, guarda una foto con ese nombre antes de continuar.")
        return

    # 1. Leer la imagen real usando OpenCV
    image = cv2.imread(IMAGE_PATH)
    height, width, channels = image.shape

    print("=== Edge Processor: Modo Imagen Real (Simulado) ===")
    print(f"Cargada imagen: {IMAGE_PATH} ({width}x{height} píxeles)")

    # 2. Simular una Bounding Box basada en el tamaño REAL de tu imagen
    # AWS Rekognition no te da píxeles, te da porcentajes (de 0 a 1) del tamaño de la foto.
    # Simularemos que la persona ocupa el centro de tu foto real:
    mock_detected_persons = [
        [0.25, 0.15, 0.50, 0.70]  # [Left, Top, Width, Height] en porcentajes
    ]

    # 3. Construir el Payload oficial estilo AWS
    payload = generate_rekognition_payload(mock_detected_persons)

    # Imprimir en consola para verificar las coordenadas calculadas
    print("\nPayload generado para Kinesis:")
    bbox = payload["Persons"][0]["Person"]["BoundingBox"]
    print(f"   Persona detectada en: Left={bbox['Left']}, Top={bbox['Top']}")
    print(f"   Tamaño relativo: Width={bbox['Width']}, Height={bbox['Height']}")

    # 4. Enviar el registro real a tu Kinesis en Docker
    print(f"\n🚀 Enviando reporte de imagen real a Kinesis [{STREAM_NAME}]...")

    try:
        response = kinesis_client.put_record(
            StreamName=STREAM_NAME,
            Data=json.dumps(payload),
            PartitionKey="static_image_test",
        )
        print(
            f"¡Enviado con éxito! SequenceNumber: {response['SequenceNumber'][:30]}..."
        )
        print(
            "Revisa tu otra terminal (el consumidor Lambda) para ver cómo procesa tu foto."
        )

    except Exception as e:
        print(f"Falló el envío a LocalStack: {e}")


if __name__ == "__main__":
    main()
