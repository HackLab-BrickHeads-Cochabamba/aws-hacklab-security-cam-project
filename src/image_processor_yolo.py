import cv2
import json
import boto3
import os
from ultralytics import YOLO
from mock_rekognition import generate_rekognition_payload

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(BASE_DIR, "assets", "random.png")
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
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Error: No encontré la imagen '{IMAGE_PATH}'")
        return

    image = cv2.imread(IMAGE_PATH)
    height, width, _ = image.shape
    print(f"📷 Analizando imagen: {IMAGE_PATH} ({width}x{height}px)")

    results = model(image, verbose=False)[0]

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

    print(f"IA finalizada. Personas detectadas en la foto: {len(detected_persons)}")

    payload = generate_rekognition_payload(detected_persons)

    try:
        response = kinesis_client.put_record(
            StreamName=STREAM_NAME,
            Data=json.dumps(payload),
            PartitionKey="yolo_image_test",
        )
        print(
            f"🚀 Datos reales de IA enviados a Kinesis. Seq: {response['SequenceNumber'][:20]}..."
        )
        print("Revisa la terminal de la Lambda para ver la respuesta dinámica.")
    except Exception as e:
        print(f"❌ Error al enviar a LocalStack: {e}")


if __name__ == "__main__":
    main()
