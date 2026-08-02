import qrcode
import json
import os


def generate_student_qr(usn, fullname, department, semester):

    qr_data = {
        "usn": usn,
        "fullname": fullname,
        "department": department,
        "semester": semester
    }

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4
    )

    qr.add_data(json.dumps(qr_data))
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")

    folder = "static/qrcodes"

    if not os.path.exists(folder):
        os.makedirs(folder)

    image.save(f"{folder}/{usn}.png")

    return f"{folder}/{usn}.png"