# Video Rekognition Project

Project dedicated to detection and tracking of persons on a covered area with cameras using AWS Services and hardware hacking

## Technologies to be used

- **Hardware & Edge:** Organization of local components (GStreamer, Python 3.12, RTSP).
- **Ingestion & Storage:** Clean separation of responsibilities between **AWS KVS** and **Amazon S3**.
- **Processing & AI:** Integration of specific Rekognition APIs (`Person Tracking`, `Face Detection`, etc.) within the real-time architecture using **Kinesis Data Streams (KDS)**.
- **Backend & Notifications:** Exact role of **AWS Lambda** and **Amazon SNS** to close the alert loop.
