import time

def generate_rekognition_payload(detected_persons):
    """
    Estructura los datos de detección locales para que coincidan 
    exactamente con el formato de AWS Rekognition Video Stream Processor.
    """
    persons_payload = []
    
    for idx, box in enumerate(detected_persons):
        # box esperado: [x_min, y_min, x_max, y_max] con valores de 0.0 a 1.0
        x1, y1, x2, y2 = box
        
        persons_payload.append({
            "TrackId": idx + 1,
            "Person": {
                "BoundingBox": {
                    "Left": round(x1, 4),
                    "Top": round(y1, 4),
                    "Width": round(x2 - x1, 4),
                    "Height": round(y2 - y1, 4)
                },
                "Confidence": 98.42
            }
        })

    return {
        "InputInformation": {
            "KinesisVideoStream": {
                "Arn": "arn:aws:kinesisvideo:us-east-1:123456789012:stream/local-edge-stream/1700000000",
                "FrameOffsetInMs": int(time.time() * 1000)
            }
        },
        "StreamProcessorInformation": {
            "Status": "RUNNING"
        },
        "FaceSearchResponse": [],
        "Persons": persons_payload
    }