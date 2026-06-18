[README.md](https://github.com/user-attachments/files/29108355/README.md)
# MSBTE Result Analyzer

This project converts a batch of MSBTE student result PDFs into one Excel workbook.

The workbook contains:

1. `Student Marks` - seat number, enrollment number, name, subject-wise marks, total marks, percentage, and result.
2. `Result Summary` - count of students in First Class with Distinction, First Class, Pass, Fail, and A.T.K.T.
3. `Out Of Marks` - students who scored full marks in any subject. A student appears multiple times if they scored full marks in multiple subjects.
4. `Top 5 Toppers` - first five toppers by percentage, then total marks.

## Run The Upload App

Use the bundled Python in this Codex workspace or any Python environment with `pdfplumber` and `openpyxl` installed.

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:8000
```

Upload all result PDFs from the same class, then download the generated Excel file.

## Run From Command Line

```powershell
python cli.py "C:\path\to\pdf-folder" -o "output\msbte_result_analysis.xlsx"
```

You can also pass a single PDF:

```powershell
python cli.py "C:\path\to\student-result.pdf"
```

## Install Dependencies

If your Python does not already have the required packages:

```powershell
pip install -r requirements.txt
```

## Scanned PDF / OCR Setup

MSBTE result PDFs that are image-scanned need OCR. This project uses the local Tesseract OCR engine for that.

Install Tesseract for Windows:

1. Download and install Tesseract OCR from the UB Mannheim Windows builds:
   `https://github.com/UB-Mannheim/tesseract/wiki`
2. During installation, allow it to add Tesseract to PATH if the installer offers that option.
3. Restart PowerShell or your terminal.
4. Check installation:

```powershell
tesseract --version
```

If Tesseract is installed but not on PATH, set its path before running the app:

```powershell
$env:TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"
python app.py
```

Useful OCR settings:

```powershell
$env:OCR_LANG = "eng"
$env:OCR_DPI = "300"
$env:TESSERACT_PSM = "6"
```

For most result PDFs, `OCR_DPI=300` and `TESSERACT_PSM=6` are a good starting point.

## Notes About PDF Formats

MSBTE result PDFs can vary by year, exam scheme, and whether the PDF is text-based or scanned.

This version supports both text-based PDFs and scanned PDFs. Scanned PDFs require Tesseract OCR. OCR is never perfect, so always verify extracted marks before using the final workbook officially. If a result PDF uses a different layout, the analyzer will still create the workbook but may show warnings for missing fields. In that case, update the patterns in `msbte_result_analyzer/parser.py`.

## Test

```powershell
python -m unittest
```
