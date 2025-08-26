import os
import fitz

RAW_DIR = "data/raw"
OUT_DIR = "data/processed"

def convert_pdfs():
    for filename in os.listdir(RAW_DIR):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(RAW_DIR, filename)
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()

            out_filename = filename.replace(".pdf", ".txt")
            with open(os.path.join(OUT_DIR, out_filename), "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Converted {filename} → {out_filename}")

if __name__ == "__main__":
    convert_pdfs()
