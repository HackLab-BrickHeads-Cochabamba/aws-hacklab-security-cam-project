import base64
import json


def lambda_handler(event, context):
    """
    Función Lambda estándar de AWS que se ejecuta automáticamente
    cada vez que Kinesis recibe nuevos registros.
    """
    print(f"=== Lambda activada! Recibidos {len(event['Records'])} registros ===")

    for record in event["Records"]:
        # 1. Kinesis envía los datos encriptados en Base64. Hay que decodificarlos.
        payload_encoded = record["kinesis"]["data"]
        payload_decoded = base64.b64decode(payload_encoded).decode("utf-8")

        # 2. Convertir el string de texto a un diccionario de Python (JSON)
        data = json.loads(payload_decoded)

        # 3. Extraer información útil del formato de Rekognition
        frame_offset = data["InputInformation"]["KinesisVideoStream"]["FrameOffsetInMs"]
        persons = data["Persons"]

        print(f"\n[PROCESANDO EVENTO] Timestamp: {frame_offset}")
        print(f"Cantidad de personas detectadas en este frame: {len(persons)}")

        for person in persons:
            track_id = person["TrackId"]
            confidence = person["Person"]["Confidence"]
            bbox = person["Person"]["BoundingBox"]

            print(
                f"  -> Persona ID {track_id} detectada con {confidence}% de confianza."
            )
            print(
                f"     Coordenadas: Top={bbox['Top']}, Left={bbox['Left']}, Width={bbox['Width']}, Height={bbox['Height']}"
            )

            # Aquí iría tu lógica de negocio real, por ejemplo:
            # - Si confidence > 90% y está en una zona prohibida -> Guardar en S3 o enviar SMS por SNS.
            if confidence > 95:
                print(
                    "  --- [ALERTA DE SEGURIDAD] Alta certeza de intrusión. Almacenando reporte... ---"
                )

    return {
        "statusCode": 200,
        "body": json.dumps("Procesamiento de Kinesis completado con éxito"),
    }
