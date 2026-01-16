"""
DD1750 Core Generation Module
Generates DD1750 forms from verified items
"""

import io
import math
from typing import List
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import pdfplumber


# DD1750 Form Layout Constants
ROWS_PER_PAGE = 18
PAGE_W, PAGE_H = 612.0, 792.0

X_BOX_L, X_BOX_R = 44.0, 88.0
X_CONTENT_L, X_CONTENT_R = 88.0, 365.0
X_UOI_L, X_UOI_R = 365.0, 408.5
X_INIT_L, X_INIT_R = 408.5, 453.5
X_SPARES_L, X_SPARES_R = 453.5, 514.5
X_TOTAL_L, X_TOTAL_R = 514.5, 566.0

Y_TABLE_TOP_LINE = 616.0
Y_TABLE_BOTTOM_LINE = 89.5
ROW_H = (Y_TABLE_TOP_LINE - Y_TABLE_BOTTOM_LINE) / ROWS_PER_PAGE
PAD_X = 3.0


def detect_bom_format(pdf_path: str) -> str:
    """
    Detect the BOM format type.
    Returns: 'TEXT_BASED', 'IMAGE_BASED', 'UNKNOWN'
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) == 0:
                return 'UNKNOWN'
            
            page = pdf.pages[0]
            text = page.extract_text()
            
            # Check if text extractable
            if not text or len(text.strip()) < 50:
                return 'IMAGE_BASED'
            
            # Has decent text content
            if 'COMPONENT LISTING' in text or 'HAND RECEIPT' in text:
                return 'TEXT_BASED'
            
            return 'TEXT_BASED' if len(text.strip()) > 200 else 'IMAGE_BASED'
            
    except Exception as e:
        print(f"Error detecting format: {e}")
        return 'UNKNOWN'


def generate_dd1750_from_verified_items(items: List, template_path: str, output_path: str):
    """
    Generate DD1750 from verified ExtractedItem objects.
    
    Args:
        items: List of ExtractedItem objects (already verified)
        template_path: Path to blank DD1750 template
        output_path: Where to save the generated DD1750
    """
    try:
        if not items:
            # If no items, just copy template
            reader = PdfReader(template_path)
            writer = PdfWriter()
            writer.add_page(reader.pages[0])
            with open(output_path, 'wb') as f:
                writer.write(f)
            return output_path, 0
        
        total_pages = math.ceil(len(items) / ROWS_PER_PAGE)
        writer = PdfWriter()
        
        for page_num in range(total_pages):
            start_idx = page_num * ROWS_PER_PAGE
            end_idx = min((page_num + 1) * ROWS_PER_PAGE, len(items))
            page_items = items[start_idx:end_idx]
            
            # Create overlay with item data
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(PAGE_W, PAGE_H))
            
            first_row_top = Y_TABLE_TOP_LINE - 5.0
            
            for i, item in enumerate(page_items):
                y = first_row_top - (i * ROW_H)
                y_desc = y - 7.0
                y_nsn = y - 12.2
                
                # Box number (line number)
                can.setFont("Helvetica", 8)
                can.drawCentredString((X_BOX_L + X_BOX_R)/2, y_desc, str(item.line_no))
                
                # Description
                can.setFont("Helvetica", 7)
                desc = item.description[:50] if len(item.description) > 50 else item.description
                can.drawString(X_CONTENT_L + PAD_X, y_desc, desc)
                
                # NSN (if available)
                if item.nsn:
                    can.setFont("Helvetica", 6)
                    can.drawString(X_CONTENT_L + PAD_X, y_nsn, f"NSN: {item.nsn}")
                
                # Unit of Issue (EA = Each)
                can.setFont("Helvetica", 8)
                can.drawCentredString((X_UOI_L + X_UOI_R)/2, y_desc, "EA")
                
                # Initial Operation quantity
                can.drawCentredString((X_INIT_L + X_INIT_R)/2, y_desc, str(item.qty))
                
                # Running Spares (always 0 for our use case)
                can.drawCentredString((X_SPARES_L + X_SPARES_R)/2, y_desc, "0")
                
                # Total quantity (same as initial for our use case)
                can.drawCentredString((X_TOTAL_L + X_TOTAL_R)/2, y_desc, str(item.qty))
            
            can.save()
            packet.seek(0)
            
            # Merge overlay with template
            overlay = PdfReader(packet)
            page = PdfReader(template_path).pages[0]
            page.merge_page(overlay.pages[0])
            writer.add_page(page)
        
        # Write final PDF
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        return output_path, len(items)
        
    except Exception as e:
        print(f"CRITICAL ERROR in DD1750 generation: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback: return blank template
        try:
            reader = PdfReader(template_path)
            writer = PdfWriter()
            writer.add_page(reader.pages[0])
            with open(output_path, 'wb') as f:
                writer.write(f)
        except:
            pass
        
        return output_path, 0
