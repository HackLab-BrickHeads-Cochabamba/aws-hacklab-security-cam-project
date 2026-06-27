import cv2
import json
import boto3
import time
from ultralytics import YOLO
from mock_rekognition import generate_rekognition_payload

STREAM_NAME = "rekognition-person-stream"

print("Cargando modelo de Inteligencia Artificial YOLOv8...")
model = YOLO("yolov8n.pt")

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

    print(f"Webcam activada correctamente ({width}x{height}px)")
    print("Haz clic en la ventana del video y presiona 'q' para cerrar la cámara.")

    frame_count = 0
    PROCESS_INTERVAL_SEC = 0.5
    last_processed_time = 0.0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error al recibir transmisión de la webcam.")
            break

        frame_count += 1
        current_time = time.time()

        # Zona segura, porcentajes porsi
        x_min, x_max = int(width * 0.20), int(width * 0.80)
        y_min, y_max = int(height * 0.20), int(height * 0.80)
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 255), 1)
        cv2.putText(
            frame,
            "ZONA CENTRAL AMPLIA",
            (x_min + 5, y_min + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (0, 255, 255),
            1,
        )

        if current_time - last_processed_time >= PROCESS_INTERVAL_SEC:
            last_processed_time = current_time

            results = model(frame, verbose=False)[0]
            detected_persons = []

            for box in results.boxes:
                class_id = int(box.cls[0])
                label = results.names[class_id]

                if label == "person":
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = round(float(box.conf[0]) * 100, 2)

                    left = round(x1 / width, 4)
                    top = round(y1 / height, 4)
                    box_width = round((x2 - x1) / width, 4)
                    box_height = round((y2 - y1) / height, 4)

                    detected_persons.append(
                        [left, top, box_width, box_height, confidence]
                    )

                    cv2.rectangle(
                        frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2
                    )
                    cv2.putText(
                        frame,
                        f"Persona: {confidence}%",
                        (int(x1), int(y1) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )

            if len(detected_persons) > 0:
                print(
                    f"[INTERVALO] Frame #{frame_count} | Personas: {len(detected_persons)}"
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

        cv2.imshow("YOLOv8 Webcam Detect - Presiona 'q' para salir", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("Webcam detenida por el usuario.")
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Programa finalizado con éxito.")


if __name__ == "__main__":
    main()
