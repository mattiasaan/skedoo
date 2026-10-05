import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\matti\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
print(pytesseract.get_tesseract_version())