"""
utils/report_generator.py
---------------------------
Helpers to convert DataFrames into downloadable bytes for:
    - CSV  (pandas built-in)
    - Excel (openpyxl engine via pandas)
    - PDF  (ReportLab table report)

All functions return `bytes` so they can be passed directly to
`st.download_button(data=...)`.
"""

import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Return CSV bytes for a DataFrame."""
    return df.to_csv(index=False).encode("utf-8")


def dataframe_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Report") -> bytes:
    """Return Excel (.xlsx) bytes for a DataFrame using openpyxl engine."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    buffer.seek(0)
    return buffer.getvalue()


def dataframe_to_pdf_bytes(df: pd.DataFrame, title: str = "Metrax Report") -> bytes:
    """Return PDF bytes containing a title and a table rendering of the DataFrame.

    Long DataFrames are rendered with a small font and landscape orientation
    to maximize column visibility.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Title"]), Spacer(1, 0.5 * cm)]

    if df.empty:
        elements.append(Paragraph("No data available.", styles["Normal"]))
    else:
        # Convert DataFrame to list-of-lists for ReportLab Table
        data = [list(df.columns)] + df.astype(str).values.tolist()

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F6FB")]),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()