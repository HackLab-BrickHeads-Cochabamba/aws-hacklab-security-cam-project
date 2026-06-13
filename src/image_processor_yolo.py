import cv2
import json
import boto3
import os
import time
from ultralytics import YOLO
from mock_rekognition import generate_rekognition_payload

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Cambia el nombre de tu archivo de video aquí
VIDEO_PATH = os.path.join(BASE_DIR, "assets", "people.mp4")
STREAM_NAME = "rekognition-person-stream"

print("🧠 Cargando modelo de Inteligencia Artificial YOLOv8...")
model = YOLO("yolov8n.pt")

kinesis_client = boto3.client(
    "kinesis",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="mock",
    aws_secret_access_key="mock",
)


def main():
    if not os.path.exists(VIDEO_PATH):
        print(f"Error: No encontré el video '{VIDEO_PATH}'")
        return

    cap = cv2.VideoCapture(VIDEO_PATH)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"🎥 Analizando video: {VIDEO_PATH} ({width}x{height}px) a {fps} FPS")

    frame_count = 0
    FRAME_INTERVAL = 10

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        if frame_count % FRAME_INTERVAL == 0:
            print(f"Procesando frame #{frame_count}...")

            results = model(frame, verbose=False)[0]
            detected_persons = []

            for box in results.boxes:
                class_id = int(box.cls[0])
                label = results.names[class_id]

                if label == "person":
                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    left = round(x1 / width, 4)
                    top = round(y1 / height, 4)
                    box_width = round((x2 - x1) / width, 4)
                    box_height = round((y2 - y1) / height, 4)

                    detected_persons.append([left, top, box_width, box_height])

            print(f"   👥 Personas detectadas en este frame: {len(detected_persons)}")

            if len(detected_persons) > 0:
                payload = generate_rekognition_payload(detected_persons)

                payload["FrameNumber"] = frame_count

                try:
                    response = kinesis_client.put_record(
                        StreamName=STREAM_NAME,
                        Data=json.dumps(payload),
                        PartitionKey="yolo_video_test",
                    )
                    print(
                        f"Datos enviados. Seq: {response['SequenceNumber'][:20]}..."
                    )
                except Exception as e:
                    print(f"   ❌ Error al enviar a LocalStack: {e}")

    cap.release()
    cv2.destroyAllWindows()
    print("🏁 Procesamiento de video finalizado.")


if __name__ == "__main__":
    main()
