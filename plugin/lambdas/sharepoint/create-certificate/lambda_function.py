# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import datetime
import json
import os
import tempfile

import boto3
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def handler(event, context):
    """Function handler."""

    print(f"Received event: {event}")
    print("Generating certificate")

    # Get bucket name from environment variables
    bucket_name = os.environ["CERTIFICATE_BUCKET_NAME"]

    # Get Azure sharepoint app client ID from event - required field
    azure_client_id = event["body-json"]["appId"]

    # Create subfolder path based on client ID
    client_folder = f"{azure_client_id}/"

    # Define file paths with client ID subfolder
    certificate_path = f"{client_folder}sharepoint.crt"
    private_key_path = f"{client_folder}private.key"

    # Get certificate parameters from event
    cert_common_name = event["body-json"].get("cert_common_name", "example.com")
    country_name = event["body-json"].get("country_name", "US")
    state_name = event["body-json"].get("state_name", "State")
    locality_name = event["body-json"].get("locality_name", "City")
    organization_name = event["body-json"].get("organization_name", "Organization")
    validity_days = event.get("validity_days", 365)

    # Create temporary directory for files
    with tempfile.TemporaryDirectory() as temp_dir:
        cert_file_path = os.path.join(temp_dir, "certificate.crt")
        key_file_path = os.path.join(temp_dir, "private_key.pem")

        # Generate private key and certificate
        private_key, certificate = generate_self_signed_cert(
            cert_common_name, country_name, state_name, locality_name, organization_name, validity_days
        )

        # Write certificate to file
        with open(cert_file_path, "wb") as cert_file:
            cert_file.write(certificate.public_bytes(encoding=serialization.Encoding.PEM))

        # Get private key bytes in PEM format
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Write private key to file
        with open(key_file_path, "wb") as key_file:
            key_file.write(private_key_bytes)

        print("Certificate and key generated. Uploading files to S3...")

        # Upload files to S3 with server-side encryption
        s3_client = boto3.client("s3")

        # Upload certificate with server-side encryption
        s3_client.upload_file(
            cert_file_path, bucket_name, certificate_path, ExtraArgs={"ServerSideEncryption": "AES256"}
        )
        print(f"Certificate uploaded to s3://{bucket_name}/{certificate_path}")

        # Upload private key with server-side encryption
        s3_client.upload_file(
            key_file_path, bucket_name, private_key_path, ExtraArgs={"ServerSideEncryption": "AES256"}
        )
        print(f"Private key uploaded to s3://{bucket_name}/{private_key_path}")

    return {
        "statusCode": 200,
        "body": {
            "certificate": {
                "uploaded": "Uploaded certificate",
                "bucket": bucket_name,
                "certificatePath": certificate_path,
                "format": "PEM encoded X.509 (.crt)",
            },
            "private_key": {
                "uploaded": "Uploaded private key",
                "bucket": bucket_name,
                "privateKeyPath": private_key_path,
                "encryption": "S3 Server-Side Encryption (AES256)",
            },
            "clientId": azure_client_id,
        },
    }


def generate_self_signed_cert(common_name, country_name, state_name, locality_name, organization_name, validity_days):
    """Function generate_self_signed_cert."""

    """
    Generate a self-signed certificate and private key
    """
    # Generate private key
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())

    # Build subject and issuer names
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.COUNTRY_NAME, country_name),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state_name),
            x509.NameAttribute(NameOID.LOCALITY_NAME, locality_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization_name),
        ]
    )

    # Certificate validity period
    now = datetime.datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=validity_days))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(common_name)]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256(), default_backend())
    )

    return private_key, cert


if __name__ == "__main__":
    os.environ["CERTIFICATE_BUCKET_NAME"] = "q-sharepoint-certificate-bucket"
    event = {"body-json": {"common_name": "example", "appId": "test-client-id"}}
    handler(event, {})
