import pandas as pd
import PyPDF2

def extract_from_pdf(file):
    text = ""
    pdf_reader = PyPDF2.PdfReader(file)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_from_excel(file):
    df = pd.read_excel(file)
    return df.to_string()
