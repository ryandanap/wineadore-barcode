import os
import tempfile

import pandas as pd
import streamlit as st

from barcode_engine import generate_pdf
from email_sender import send_email_with_attachment


st.set_page_config(
    page_title="Wine Adore Barcode Generator",
    page_icon="🍷",
    layout="centered"
)

st.title("🍷 Wine Adore Barcode Generator")

st.write(
    "Upload Excel file yang berisi SKU, Wine Name, dan Barcode."
)

# PDF hasil generate disimpan di session_state agar tetap "ingat"
# walau halaman rerun (misalnya saat tombol "Kirim Email" diklik,
# yang merupakan interaksi terpisah dari tombol "Generate PDF").
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

uploaded_file = st.file_uploader(
    "Upload Excel",
    type=["xlsx"]
)

if uploaded_file:

    try:

        df = pd.read_excel(uploaded_file)

        required_columns = [
            "SKU",
            "Wine Name",
            "Barcode"
        ]

        missing = [
            col
            for col in required_columns
            if col not in df.columns
        ]

        if missing:

            st.error(
                f"Missing columns: {', '.join(missing)}"
            )

            st.stop()

        st.success(
            f"{len(df)} wine(s) loaded"
        )

        st.dataframe(
            df.head(20),
            use_container_width=True
        )

        if st.button(
            "Generate PDF",
            type="primary"
        ):

            with st.spinner(
                "Generating barcode labels..."
            ):

                temp_pdf = os.path.join(
                    tempfile.gettempdir(),
                    "Wine_Barcodes.pdf"
                )

                generate_pdf(
                    df,
                    temp_pdf
                )

                with open(
                    temp_pdf,
                    "rb"
                ) as f:

                    st.session_state.pdf_bytes = f.read()

                st.success(
                    "PDF generated successfully!"
                )

    except Exception as e:

        st.error(str(e))


# ==================================================
# Tombol Download & form Kirim Email -- hanya muncul
# kalau PDF sudah berhasil dibuat
# ==================================================

if st.session_state.pdf_bytes:

    st.download_button(
        label="📥 Download PDF",
        data=st.session_state.pdf_bytes,
        file_name="Wine_Barcodes.pdf",
        mime="application/pdf"
    )

    st.divider()
    st.subheader("📧 Kirim PDF via Email")

    to_email = st.text_input(
        "Kirim ke (To)",
        value="hosting.team@wineadore.com"
    )

    from_email = st.text_input(
        "Kirim dari (From)",
        value="procurement@wineadore.com"
    )

    # Default email template — editable by the user before sending
    DEFAULT_SUBJECT = "Barcode for Wine Tasting Line Up (12-14 June)"
    DEFAULT_BODY = (
        "Dear Singapore Team,\n\n"
        "Here are the barcodes,\n\n"
        "Kindly scan each barcode, and if any of them do not work "
        "or show a different product, please let me know immediately.\n\n"
        "Warm Regards,\n"
        "Product Team"
    )

    email_subject = st.text_input(
        "Subject",
        value=DEFAULT_SUBJECT
    )

    email_body = st.text_area(
        "Message",
        value=DEFAULT_BODY,
        height=220
    )

    st.caption(
        "✏️ You can edit the subject and message above before sending. "
        "The PDF will be attached automatically."
    )

    if st.button("Kirim Email"):

        if not email_subject.strip():
            st.warning("Please enter an email subject before sending.")
            st.stop()

        if not email_body.strip():
            st.warning("Please enter a message before sending.")
            st.stop()

        try:

            with st.spinner("Mengirim email..."):

                send_email_with_attachment(
                    smtp_server=st.secrets["email"]["smtp_server"],
                    smtp_port=st.secrets["email"]["smtp_port"],
                    sender_email=from_email,
                    sender_password=st.secrets["email"]["smtp_password"],
                    recipient_email=to_email,
                    subject=email_subject,
                    body=email_body,
                    attachment_bytes=st.session_state.pdf_bytes,
                    attachment_filename="Wine_Barcodes.pdf"
                )

            st.success(
                f"Email berhasil dikirim ke {to_email}!"
            )

        except Exception as e:

            st.error(
                f"Gagal mengirim email: {e}"
            )
