from mocks.gcp.firebase_admin import messaging as m
from firebase_admin.credentials import Certificate

messaging = m

cert_captured: Certificate = None


def initialize_app(cert: Certificate):
    cert_captured = cert
    return {}
