import boto3
import time
import base64  # 👈 Añadimos esta librería para la conversión
from lambda_processor import lambda_handler

STREAM_NAME = "rekognition-person-stream"

kinesis_client = boto3.client(
    "kinesis",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="mock",
    aws_secret_access_key="mock",
)


def main():
    print(f"=== Escuchando Kinesis Stream: {STREAM_NAME} ===")

    response = kinesis_client.describe_stream(StreamName=STREAM_NAME)
    shard_id = response["StreamDescription"]["Shards"][0]["ShardId"]

    shard_iterator_resp = kinesis_client.get_shard_iterator(
        StreamName=STREAM_NAME, ShardId=shard_id, ShardIteratorType="LATEST"
    )
    shard_iterator = shard_iterator_resp["ShardIterator"]

    while True:
        records_response = kinesis_client.get_records(
            ShardIterator=shard_iterator, Limit=10
        )
        records = records_response["Records"]

        if records:
            mock_records = []
            for record in records:
                # Convertimos los bytes puros de Kinesis a un string Base64 real
                # tal como lo haría AWS al invocar una Lambda en producción.
                b64_data = base64.b64encode(record["Data"]).decode("utf-8")

                mock_records.append({"kinesis": {"data": b64_data}})

            mock_lambda_event = {"Records": mock_records}

            # Invocar a la Lambda
            lambda_handler(mock_lambda_event, None)

        shard_iterator = records_response["NextShardIterator"]
        time.sleep(1)


if __name__ == "__main__":
    main()
