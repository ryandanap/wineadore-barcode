import os
import tempfile

from PIL import Image

from barcode import EAN13, Code128
from barcode.writer import ImageWriter

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


# ==================================================
# LABEL CONFIG
# ==================================================

LABEL_WIDTH = 105 * mm
LABEL_HEIGHT = 74 * mm

COLS = 2
ROWS = 4

FONT_NAME = "Helvetica"
FONT_SIZE = 10

# Font & jarak khusus untuk teks nomor barcode (digambar manual,
# TERPISAH dari gambar barcode, agar tidak pernah menyatu/tumpang
# tindih dengan batang barcode).
NUMBER_FONT_NAME = "Helvetica-Bold"
NUMBER_FONT_SIZE = 12
NUMBER_GAP_MM = 6  # jarak antara batang barcode dan nomor di bawahnya


# ==================================================
# HELPERS
# ==================================================

def clean_barcode(value):

    value = str(value).strip()

    if value.endswith(".0"):
        value = value[:-2]

    return value


def format_ean13_number(value):
    """
    Memformat angka EAN-13 menjadi tampilan standar industri,
    sama seperti yang ditampilkan generator Zoho:
    digit pertama berdiri sendiri, lalu dua kelompok berisi 6 digit.

    Contoh: '5601237001065' -> '5  601237  001065'

    Untuk kode non-EAN13 (Code128 dsb.), nilai dikembalikan apa adanya.
    """
    if len(value) == 13 and value.isdigit():
        return f"{value[0]}  {value[1:7]}  {value[7:]}"
    return value


def create_barcode(barcode_value, file_path):
    """
    Membuat GAMBAR BARCODE SAJA (tanpa teks bawaan library).
    Teks angka digambar terpisah belakangan di generate_pdf(),
    sehingga posisinya bisa dikontrol penuh dan tidak akan pernah
    menyatu/tumpang tindih dengan batang barcode.

    Mengembalikan kode final yang benar-benar dipakai oleh barcode
    (termasuk check digit hasil perhitungan ulang library untuk
    EAN-13), agar teks yang ditampilkan SELALU sinkron dengan
    barcode yang sebenarnya bisa di-scan.
    """

    writer_options = {
        "module_width": 0.25,
        "module_height": 15,
        "quiet_zone": 2,
        "write_text": False,   # <-- KUNCI PERBAIKAN: matikan teks bawaan
        "dpi": 600
    }

    if barcode_value.isdigit() and len(barcode_value) == 13:

        # python-barcode mengharapkan 12 digit lalu menghitung
        # sendiri check digit ke-13 -> hasil akhirnya diambil lewat
        # get_fullcode() agar teks yang ditampilkan pasti akurat.
        barcode_obj = EAN13(
            barcode_value[:-1],
            writer=ImageWriter()
        )

    else:

        barcode_obj = Code128(
            barcode_value,
            writer=ImageWriter()
        )

    barcode_obj.save(
        file_path,
        options=writer_options
    )

    return barcode_obj.get_fullcode()


def draw_wrapped_text(
    pdf,
    text,
    center_x,
    start_y,
    max_width
):

    words = text.split()

    lines = []
    current = ""

    for word in words:

        test = f"{current} {word}".strip()

        if pdf.stringWidth(
            test,
            FONT_NAME,
            FONT_SIZE
        ) <= max_width:

            current = test

        else:

            lines.append(current)
            current = word

    if current:
        lines.append(current)

    line_height = 11

    for i, line in enumerate(lines):

        pdf.drawCentredString(
            center_x,
            start_y - (i * line_height),
            line
        )


# ==================================================
# MAIN PDF GENERATOR
# ==================================================

def generate_pdf(df, output_pdf):

    page_width, page_height = A4

    pdf = canvas.Canvas(
        output_pdf,
        pagesize=A4
    )

    temp_dir = tempfile.mkdtemp()

    records = df.to_dict("records")

    for idx, row in enumerate(records):

        page_position = idx % (ROWS * COLS)

        if idx > 0 and page_position == 0:
            pdf.showPage()

        row_pos = page_position // COLS
        col_pos = page_position % COLS

        x = col_pos * LABEL_WIDTH
        y = page_height - ((row_pos + 1) * LABEL_HEIGHT)

        # Border

        pdf.rect(
            x,
            y,
            LABEL_WIDTH,
            LABEL_HEIGHT,
            stroke=1,
            fill=0
        )

        wine_name = str(row["Wine Name"]).strip()
        barcode_value = clean_barcode(row["Barcode"])

        try:

            barcode_file = os.path.join(
                temp_dir,
                f"barcode_{idx}"
            )

            # Buat gambar barcode (bars only) + ambil kode final
            final_code = create_barcode(
                barcode_value,
                barcode_file
            )

            barcode_png = barcode_file + ".png"

            # ==========================
            # KEEP ORIGINAL PROPORTION
            # ==========================

            img = Image.open(barcode_png)

            img_width, img_height = img.size

            target_width = 60 * mm

            target_height = (
                target_width *
                img_height /
                img_width
            )

            barcode_x = x + (
                (LABEL_WIDTH - target_width) / 2
            )

            barcode_y = y + 30 * mm

            pdf.drawImage(
                barcode_png,
                barcode_x,
                barcode_y,
                width=target_width,
                height=target_height,
                mask="auto"
            )

            # ==========================
            # NOMOR BARCODE (digambar TERPISAH, format EAN-13 rapi
            # seperti tampilan Zoho: "5  601237  001065")
            # ==========================

            display_text = format_ean13_number(final_code)

            number_y = barcode_y - (NUMBER_GAP_MM * mm)

            pdf.setFont(
                NUMBER_FONT_NAME,
                NUMBER_FONT_SIZE
            )

            pdf.drawCentredString(
                x + (LABEL_WIDTH / 2),
                number_y,
                display_text
            )

        except Exception as e:

            print(
                f"Barcode error {barcode_value}: {e}"
            )

        # ==========================
        # WINE NAME
        # ==========================

        pdf.setFont(
            FONT_NAME,
            FONT_SIZE
        )

        draw_wrapped_text(
            pdf,
            wine_name,
            x + (LABEL_WIDTH / 2),
            y + 12 * mm,
            LABEL_WIDTH - (12 * mm)
        )

    pdf.save()

    return output_pdf