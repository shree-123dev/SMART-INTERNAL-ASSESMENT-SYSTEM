import os
import qrcode
from PIL import Image


def generate_student_qr(usn, fullname=None, department=None, semester=None):
    """
    Generates a unique QR code for a student identifying them by their USN.
    Stores the QR image in static/qr/<USN>.png and returns the relative path.
    """
    if not usn:
        raise ValueError("USN is required to generate a student QR code.")

    usn_clean = str(usn).strip().upper()

    # The QR code identifies the student by their USN
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(usn_clean)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    folder = os.path.join("static", "qr")
    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(folder, f"{usn_clean}.png").replace("\\", "/")
    img.save(file_path)

    return file_path


def ensure_student_qr(usn, fullname=None, department=None, semester=None):
    """
    Ensures that a student's QR image file exists on disk.
    If it is missing or invalid, regenerates it.
    """
    if not usn:
        return None

    usn_clean = str(usn).strip().upper()
    file_path = os.path.join("static", "qr", f"{usn_clean}.png").replace("\\", "/")

    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return generate_student_qr(usn_clean, fullname, department, semester)

    return file_path