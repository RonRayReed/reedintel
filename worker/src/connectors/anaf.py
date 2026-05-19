from db import insert_source_record


def validate_vat(vat_number: str):
    # Configure ANAF endpoint and authentication before use.
    # Store credentials in Key Vault. Never hardcode credentials here.
    raise NotImplementedError("Configure ANAF endpoint and authentication before use.")


def run():
    return {"source": "ANAF", "status": "connector_skeleton_ready"}
