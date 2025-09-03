import sys
from pathlib import Path

pdf_path = Path('/mnt/c/Users/DzunisaniM/KasiKash/mechanic_bank_statement.pdf')

print('[INFO] Testing PDF extraction for:', pdf_path)

py_text = ''
try:
    import PyPDF2
    with open(pdf_path, 'rb') as f:
        r = PyPDF2.PdfReader(f)
        for i, page in enumerate(r.pages):
            t = page.extract_text() or ''
            if t.strip():
                py_text += f"\n[PDF Page {i+1} Text]\n" + t + "\n"
    print('PYPDF2_LEN', len(py_text))
    print(py_text[:800])
except Exception as e:
    print('PYPDF2_ERR', e)

ocr_text_all = ''
try:
    from pdf2image import convert_from_bytes
    import pytesseract
    with open(pdf_path, 'rb') as f:
        imgs = convert_from_bytes(f.read())
    for i, img in enumerate(imgs):
        try:
            ocr = pytesseract.image_to_string(img)
            if ocr.strip():
                ocr_text_all += f"\n[OCR {i+1}]\n" + ocr + "\n"
        except Exception as e:
            print(f'OCR_PAGE_ERR {i+1}', e)
    print('OCR_LEN', len(ocr_text_all))
    print(ocr_text_all[:800])
except Exception as e:
    print('OCR_PIPE_ERR', e)

print('[DONE]')


