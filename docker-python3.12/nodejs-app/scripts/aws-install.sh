#!/usr/bin/bash

sudo yum remove awscli

curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

aws configure

aws configure list

Создайте очередь с именем sample-queue:
aws sqs create-queue \
  --queue-name sample-queue \
  --endpoint https://message-queue.api.cloud.yandex.net/


{
    "QueueUrl": "https://message-queue.api.cloud.yandex.net/b1gib03pgvqrrfvhl3kb/dj6000000075tj270146/sample-queue"
}

Отправьте сообщение в созданную очередь, используя сохраненный ранее URL очереди:
export ENDPOINT=https://message-queue.api.cloud.yandex.net/
export QUEUEURL=https://message-queue.api.cloud.yandex.net/b1gib03pgvqrrfvhl3kb/dj6000000075tj270146/sample-queue


aws sqs send-message \
  --message-body "сообщение 1" \
  --endpoint ${ENDPOINT} \
  --queue-url ${QUEUEURL}

{
    "MD5OfMessageBody": "753c414a83923ee88b0311f1449f4a7e",
    "MessageId": "852065d6-f23eacac-17dda229-75754d92",
    "SequenceNumber": "0"
}

aws sqs send-message \
  --message-body "сообщение 2" \
  --endpoint ${ENDPOINT} \
  --queue-url ${QUEUEURL}

--message-body "сообщение 2" \
  --endpoint ${ENDPOINT} \
  --queue-url ${QUEUEURL}
{
    "MD5OfMessageBody": "f16c3291770ac45ce081387078dd0176",
    "MessageId": "41368d79-acc411d3-d9e7e927-9e05d3f2",
    "SequenceNumber": "0"
}

Примите сообщение из очереди:

export ENDPOINT=https://message-queue.api.cloud.yandex.net/
export QUEUEURL=https://message-queue.api.cloud.yandex.net/b1gib03pgvqrrfvhl3kb/dj6000000075tj270146/sample-queue


aws sqs receive-message --endpoint ${ENDPOINT} --queue-url ${QUEUEURL}
aws sqs receive-message --endpoint https://message-queue.api.cloud.yandex.net/ --queue-url https://message-queue.api.cloud.yandex.net/b1gib03pgvqrrfvhl3kb/dj6000000075tj270146/sample-queue

"ReceiptHandle": "EAEgqpCetJYzKAA",
"ReceiptHandle": "EAEgqpCetJYzKAA"
"ReceiptHandle": "EAEg0bGotJYzKAI",


далите полученное сообщение из очереди:
aws sqs delete-message \
  --queue-url "https://message-queue.api.cloud.yandex.net/b1gib03pgvqrrfvhl3kb/dj6000000075tj270146/sample-queue" \
  --endpoint https://message-queue.api.cloud.yandex.net/ \
  --receipt-handle "EAEg0bGotJYzKAI"
