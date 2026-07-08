import os
import uuid


def save_receipt_file(file_storage, *, upload_root: str, user_id: int) -> dict:
    """Save uploaded receipt file to disk and return metadata.

    upload_root: absolute path where uploads are stored.
    """
    os.makedirs(upload_root, exist_ok=True)

    ext = os.path.splitext(file_storage.filename)[1].lower()
    filename = f"{user_id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_root, filename)
    file_storage.save(file_path)

    return {
        "filename": filename,
        "path": file_path,
        "mimetype": file_storage.mimetype,
        "size": getattr(file_storage, "content_length", None),
    }

