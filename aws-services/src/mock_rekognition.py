import time


def generate_rekognition_payload(detected_persons):
    persons_payload = []

    for idx, box in enumerate(detected_persons):
        left, top, box_width, box_height, confidence = box

        persons_payload.append(
            {
                "TrackId": idx + 1,
                "Person": {
                    "BoundingBox": {
                        "Left": left,
                        "Top": top,
                        "Width": box_width,
                        "Height": box_height,
                    },
                    "Confidence": confidence,
                },
            }
        )

    return {
        "InputInformation": {
            "KinesisVideoStream": {
                "Arn": "arn:aws:kinesisvideo:us-east-1:123456789012:stream/rekognition-person-stream",
                "FrameOffsetInMs": int(time.time() * 1000),
            }
        },
        "StreamProcessorInformation": {"Status": "RUNNING"},
        "FaceSearchResponse": [],
        "Persons": persons_payload,
    }
