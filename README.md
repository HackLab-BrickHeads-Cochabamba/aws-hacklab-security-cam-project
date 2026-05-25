# Video Rekognition Project

Project dedicated to detection and tracking of persons on a covered area with cameras using AWS Services and hardware hacking

## Technologies to be used

- **Hardware & Edge:** Organización de los componentes locales (GStreamer, Python 3.12, RTSP).
- **Ingesta y Almacenamiento:** Separación limpia de las responsabilidades de **AWS KVS** y **Amazon S3**.
- **Procesamiento e IA:** Fusión de las APIs específicas de Rekognition (`Person Tracking`, `Face Detection`, etc.) dentro de la arquitectura de tiempo real usando **Kinesis Data Streams (KDS)**.
- **Backend y Notificaciones:** Rol exacto de **AWS Lambda** y **Amazon SNS** para cerrar el circuito de alertas.
