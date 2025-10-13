#!/usr/bin/env bash

chown mysql:mysql /certs/ca.pem /certs/server-cert.pem /certs/server-key.pem
chmod 644 /certs/ca.pem /certs/server-cert.pem
chmod 600 /certs/server-key.pem