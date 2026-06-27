import cv2
import json
import boto3
from ultralytics import YOLO
from mock_rekognition import generate_rekognition_payload

STREAM_NAME = "rekognition-person-stream"

print("🧠 Cargando modelo de Inteligencia Artificial YOLOv8...")
model = YOLO("../models/yolov8n.pt")

kinesis_client = boto3.client(
    "kinesis",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="mock",
    aws_secret_access_key="mock",
)


def main():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: No se pudo acceder a la webcam.")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"🎥 Webcam activada correctamente ({width}x{height}px)")
    print("⌨️  Haz clic en la ventana del video y presiona 'q' para cerrar la cámara.")

    frame_count = 0

    FRAME_INTERVAL = 1

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error al recibir transmisión de la webcam.")
            break

        frame_count += 1

        if frame_count % FRAME_INTERVAL == 0:
            results = model(frame, verbose=False)[0]
            detected_persons = []

            for box in results.boxes:
                class_id = int(box.cls[0])
                label = results.names[class_id]

                if label == "person":
                    # Coordenadas absolutas de la caja de detección
                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    left = round(x1 / width, 4)
                    top = round(y1 / height, 4)
                    box_width = round((x2 - x1) / width, 4)
                    box_height = round((y2 - y1) / height, 4)

                    detected_persons.append([left, top, box_width, box_height])

                    # Dibujar cuadro verde (0, 255, 0)
                    cv2.rectangle(
                        frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2
                    )
                    # Dibujar texto arriba del cuadro
                    cv2.putText(
                        frame,
                        "Persona",
                        (int(x1), int(y1) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )

            # Si hay personas en este frame, enviamos la alerta a Kinesis
            if len(detected_persons) > 0:
                print(
                    f"Frame #{frame_count} | Personas en directo: {len(detected_persons)}"
                )
                payload = generate_rekognition_payload(detected_persons)
                payload["FrameNumber"] = frame_count

                try:
                    kinesis_client.put_record(
                        StreamName=STREAM_NAME,
                        Data=json.dumps(payload),
                        PartitionKey="yolo_webcam_test",
                    )
                except Exception as e:
                    print(f"Error al enviar a LocalStack: {e}")

        # 📺 Mostrar la transmisión de la cámara con los dibujos aplicados
        cv2.imshow("YOLOv8 Webcam Detect - Presiona 'q' para salir", frame)

        # En webcam usamos cv2.waitKey(1) para que el refresco sea lo más rápido posible (1ms)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("Webcam detenida por el usuario.")
            break

    # Limpieza absoluta de la cámara
    cap.release()
    cv2.destroyAllWindows()
    print("🏁 Programa finalizado con éxito.")


if __name__ == "__main__":
    main()
