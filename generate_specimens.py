import pymupdf as fitz
from pathlib import Path

def create_specimen_pdfs():
    out_dir = Path("static/specimens")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    specimens = [
        ("Vellum_Grotesk_Specimen.pdf", "VELLUM GROTESK NO. 01", "A high-contrast display neo-grotesque engineered for large-format editorial print and tight typographic tracking."),
        ("Monograph_Serif_Specimen.pdf", "MONOGRAPH SERIF (18pt-72pt)", "An opinionated transitional serif with sharp bracketed serifs, razor ascenders, and high ink-trap definition."),
        ("Atelier_Mono_Specimen.pdf", "ATELIER MONO DISPLAY", "Technical monospace letterforms derived from Swiss architectural drafting ledgers.")
    ]
    
    f_helv = fitz.Font("helv")
    f_times = fitz.Font("tiro") # times roman
    
    for filename, title, desc in specimens:
        doc = fitz.open()
        page = doc.new_page(width=595, height=842) # A4
        page.insert_font(fontname="helv", fontbuffer=f_helv.buffer)
        page.insert_font(fontname="tiro", fontbuffer=f_times.buffer)
        
        # Draw minimalist editorial poster frame
        rect = fitz.Rect(40, 40, 555, 802)
        page.draw_rect(rect, color=(0.1, 0.1, 0.1), width=1.5)
        
        page.insert_text((60, 100), "VELLUM TYPE FOUNDRY — MONOGRAPH SPECIMEN RELEASE", fontname="helv", fontsize=10, color=(0.4, 0.4, 0.4))
        page.insert_text((60, 180), title, fontname="tiro", fontsize=24, color=(0.05, 0.05, 0.05))
        page.insert_text((60, 240), desc, fontname="helv", fontsize=11, color=(0.25, 0.25, 0.25))
        
        # Alphabet sample
        page.insert_text((60, 340), "Aa Bb Cc Dd Ee Ff Gg Hh Ii Jj Kk Ll Mm", fontname="helv", fontsize=18, color=(0.1, 0.1, 0.1))
        page.insert_text((60, 380), "Nn Oo Pp Qq Rr Ss Tt Uu Vv Ww Xx Yy Zz", fontname="helv", fontsize=18, color=(0.1, 0.1, 0.1))
        page.insert_text((60, 430), "0 1 2 3 4 5 6 7 8 9 & § @ € $ £ % * ¶", fontname="tiro", fontsize=16, color=(0.3, 0.3, 0.3))
        
        # Grid line
        page.draw_line((60, 500), (535, 500), color=(0.7, 0.7, 0.7), width=0.5)
        page.insert_text((60, 540), "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG", fontname="tiro", fontsize=18, color=(0.05, 0.05, 0.05))
        page.insert_text((60, 580), "Heavy ink trap density with optical rhythm for high-contrast print.", fontname="helv", fontsize=12, color=(0.3, 0.3, 0.3))
        
        page.insert_text((60, 780), "PRINT MONOGRAPH ED. 2026 · VELLUM PRESS · ALL RIGHTS RESERVED", fontname="helv", fontsize=8, color=(0.5, 0.5, 0.5))
        
        out_path = out_dir / filename
        doc.save(str(out_path))
        print(f"Created specimen: {out_path}")

if __name__ == "__main__":
    create_specimen_pdfs()
