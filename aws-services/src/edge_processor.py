import cv2
import json
import time
import boto3
from mock_rekognition import generate_rekognition_payload

# CONFIGURACIÓN
VIDEO_SOURCE = 0  # 0 para webcam, o ruta a un "video.mp4"
STREAM_NAME = "rekognition-person-stream"

# Inicializar el cliente de Kinesis apuntando a LocalStack
# Usamos credenciales ficticias porque LocalStack no las valida, pero boto3 las exige.
kinesis_client = boto3.client(
    "kinesis",
    endpoint_url="http://localhost:4566",  # El puerto de tu contenedor Docker
    region_name="us-east-1",
    aws_access_key_id="mock",
    aws_secret_access_key="mock",
)


def main():
    cap = cv2.VideoCapture(VIDEO_SOURCE)

    if not cap.isOpened():
        print(f"Error: No se pudo abrir la fuente de video: {VIDEO_SOURCE}")
        return

    print("=== Edge Processor Transmitiendo a LocalStack Kinesis ===")
    print(f"Enviando datos al stream: {STREAM_NAME}")
    print("Presiona Ctrl+C para detener el script.\n")

    frame_count = 0

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Fin del archivo de video o cámara desconectada.")
                break

            frame_count += 1

            # SIMULACIÓN DE DETECCIÓN (Persona en pantalla cada 15 frames)
            detected_persons = []
            if frame_count % 15 == 0:
                detected_persons.append([0.35, 0.20, 0.65, 0.85])

            # Si hay detecciones, enviamos el JSON estilo AWS a Kinesis
            if detected_persons:
                payload = generate_rekognition_payload(detected_persons)

                print(
                    f"[FRAME {frame_count}] Persona detectada. Enviando a Kinesis..."
                )

                # ENVIAR DATO A KINESIS
                response = kinesis_client.put_record(
                    StreamName=STREAM_NAME,
                    Data=json.dumps(payload),
                    PartitionKey=str(
                        payload["InputInformation"]["KinesisVideoStream"][
                            "FrameOffsetInMs"
                        ]
                    ),
                )

                print(
                    f"Registro enviado exitosamente. SequenceNumber: {response['SequenceNumber'][:30]}..."
                )
                print("-" * 60)

            time.sleep(0.033)  # Simular ~30 FPS

    except KeyboardInterrupt:
        print("\nTransmisión detenida por el usuario.")
    finally:
        cap.release()
        print("Recursos liberados.")


if __name__ == "__main__":
    main()
