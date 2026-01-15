"""
OCR Module for DD1750 BOM Extraction
Accuracy-First Design: All extractions require human verification
"""

import re
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from pdf2image import convert_from_path
from PIL import Image
import pytesseract


@dataclass
class ExtractedItem:
    """Represents an item extracted from BOM with confidence scores."""
    line_no: int
    description: str
    nsn: str
    qty: int
    
    # Confidence scores (0-100)
    description_confidence: float = 0.0
    nsn_confidence: float = 0.0
    qty_confidence: float = 0.0
    
    # Flags for review
    needs_review: bool = True
    review_notes: List[str] = field(default_factory=list)
    
    @property
    def overall_confidence(self) -> float:
        """Calculate overall confidence score."""
        return (self.description_confidence + self.nsn_confidence + self.qty_confidence) / 3
    
    def add_review_note(self, note: str):
        """Add a note explaining why this item needs review."""
        self.review_notes.append(note)
        self.needs_review = True


def preprocess_image(image: Image.Image) -> np.ndarray:
    """
    Preprocess image for better OCR accuracy.
    
    Steps:
    1. Convert to grayscale
    2. Increase contrast
    3. Denoise
    4. Binarize (black and white)
    """
    # Convert PIL to OpenCV format
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Increase contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(gray)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(contrast, None, 10, 7, 21)
    
    # Binarization - Otsu's method automatically finds optimal threshold
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary


def extract_text_with_confidence(image: np.ndarray) -> Tuple[str, Dict]:
    """
    Extract text from preprocessed image with confidence data.
    
    Returns:
        Tuple of (extracted_text, confidence_data)
    """
    # Get detailed OCR data including confidence scores
    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    
    # Build text with confidence tracking
    text_lines = []
    confidence_map = {}
    
    current_line = []
    current_line_num = -1
    
    for i in range(len(ocr_data['text'])):
        word = ocr_data['text'][i].strip()
        conf = int(ocr_data['conf'][i])
        line_num = ocr_data['line_num'][i]
        
        if word:  # Skip empty words
            if line_num != current_line_num:
                if current_line:
                    text_lines.append(' '.join(current_line))
                current_line = [word]
                current_line_num = line_num
            else:
                current_line.append(word)
            
            # Track confidence for this word
            confidence_map[word] = conf
    
    if current_line:
        text_lines.append(' '.join(current_line))
    
    full_text = '\n'.join(text_lines)
    
    return full_text, confidence_map


def validate_nsn(nsn: str) -> Tuple[bool, float]:
    """
    Validate NSN format and return confidence.
    
    NSN should be 8-9 digits.
    Returns (is_valid, confidence_score)
    """
    if not nsn:
        return False, 0.0
    
    # Check if it's all digits
    if not nsn.isdigit():
        return False, 0.0
    
    # Check length
    length = len(nsn)
    if length == 9:
        return True, 100.0
    elif length == 8:
        return True, 90.0  # Might be missing leading zero
    elif 7 <= length <= 10:
        return True, 60.0  # Possibly OCR error
    else:
        return False, 0.0


def validate_quantity(qty_str: str) -> Tuple[bool, int, float]:
    """
    Validate quantity and return confidence.
    
    Returns (is_valid, quantity, confidence_score)
    """
    if not qty_str:
        return False, 0, 0.0
    
    # Try to extract number
    match = re.search(r'(\d+)', qty_str.strip())
    if not match:
        return False, 0, 0.0
    
    qty = int(match.group(1))
    
    # Validate reasonable range
    if 1 <= qty <= 1000:
        confidence = 100.0
    elif 1001 <= qty <= 10000:
        confidence = 70.0  # Unusual but possible
    else:
        confidence = 30.0  # Very unusual, likely OCR error
    
    return True, qty, confidence


def extract_table_from_text(text: str, confidence_map: Dict[str, int]) -> List[Dict]:
    """
    Parse OCR'd text to extract table data.
    
    This is the intelligent parser that understands BOM structure.
    """
    lines = text.split('\n')
    items = []
    
    # Look for patterns that indicate a BOM item row
    # Pattern: Material/NIIN, then Description, then quantities
    
    for i, line in enumerate(lines):
        # Look for NIIN (8-9 digit number)
        nsn_matches = re.findall(r'\b(\d{8,9})\b', line)
        
        if not nsn_matches:
            continue
        
        nsn = nsn_matches[0]
        
        # Try to find description on this line or nearby lines
        # Description is usually all caps or mixed case text
        desc_match = re.search(r'([A-Z][A-Z\s,\-]{10,})', line)
        description = ""
        
        if desc_match:
            description = desc_match.group(1).strip()
        else:
            # Look at next line for description
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                desc_match = re.search(r'([A-Z][A-Z\s,\-]{10,})', next_line)
                if desc_match:
                    description = desc_match.group(1).strip()
        
        if not description:
            continue
        
        # Look for quantity - usually at end of line or next line
        # Look for "Auth Qty" column or just numbers
        qty = 1  # Default
        qty_confidence = 50.0  # Default if we can't find it
        
        # Search this line and next 2 lines for quantity
        search_text = line
        if i + 1 < len(lines):
            search_text += " " + lines[i + 1]
        if i + 2 < len(lines):
            search_text += " " + lines[i + 2]
        
        # Look for Auth Qty pattern
        qty_match = re.search(r'Auth\s+Qty\s*[:\-]?\s*(\d+)', search_text, re.IGNORECASE)
        if not qty_match:
            # Look for any standalone number (1-100 range)
            all_nums = re.findall(r'\b(\d{1,3})\b', search_text)
            if all_nums:
                # Take last number (usually quantity is at end)
                for num in reversed(all_nums):
                    if num != nsn and 1 <= int(num) <= 100:
                        qty_match = (int(num),)
                        break
        
        if qty_match:
            qty = int(qty_match[0]) if isinstance(qty_match, tuple) else int(qty_match.group(1))
            _, _, qty_confidence = validate_quantity(str(qty))
        
        # Calculate confidence scores
        nsn_valid, nsn_conf = validate_nsn(nsn)
        
        # Description confidence based on OCR word confidences
        desc_words = description.split()
        desc_confidences = [confidence_map.get(word, 50) for word in desc_words]
        desc_conf = sum(desc_confidences) / len(desc_confidences) if desc_confidences else 50.0
        
        items.append({
            'nsn': nsn,
            'description': description,
            'qty': qty,
            'nsn_confidence': nsn_conf,
            'description_confidence': desc_conf,
            'qty_confidence': qty_confidence,
        })
    
    return items


def extract_items_with_ocr(pdf_path: str, start_page: int = 0) -> List[ExtractedItem]:
    """
    Main OCR extraction function.
    
    Extracts items from image-based PDF and returns with confidence scores.
    ALL items are marked for review by default.
    """
    print(f"\n{'='*80}")
    print("OCR EXTRACTION - ACCURACY FIRST MODE")
    print(f"{'='*80}")
    
    items = []
    
    try:
        # Convert PDF to images
        print(f"\nConverting PDF to images...")
        images = convert_from_path(pdf_path, dpi=300)  # High DPI for better accuracy
        print(f"  Converted {len(images)} pages")
        
        # Process each page
        for page_num, image in enumerate(images[start_page:], start=start_page + 1):
            print(f"\n--- Processing Page {page_num} ---")
            
            # Preprocess image
            print("  Preprocessing image for OCR...")
            processed = preprocess_image(image)
            
            # Extract text with confidence
            print("  Running OCR...")
            text, confidence_map = extract_text_with_confidence(processed)
            
            print(f"  Extracted {len(text)} characters")
            
            # Parse table structure
            print("  Parsing table structure...")
            page_items = extract_table_from_text(text, confidence_map)
            
            print(f"  Found {len(page_items)} potential items")
            
            # Convert to ExtractedItem objects with review flags
            for item_data in page_items:
                item = ExtractedItem(
                    line_no=len(items) + 1,
                    description=item_data['description'],
                    nsn=item_data['nsn'],
                    qty=item_data['qty'],
                    description_confidence=item_data['description_confidence'],
                    nsn_confidence=item_data['nsn_confidence'],
                    qty_confidence=item_data['qty_confidence'],
                )
                
                # Add review notes based on confidence
                if item.nsn_confidence < 100:
                    item.add_review_note(f"NSN confidence: {item.nsn_confidence:.0f}% - Verify accuracy")
                
                if item.description_confidence < 80:
                    item.add_review_note(f"Description confidence: {item.description_confidence:.0f}% - Check for OCR errors")
                
                if item.qty_confidence < 90:
                    item.add_review_note(f"Quantity confidence: {item.qty_confidence:.0f}% - Verify count")
                
                # Always mark for review (accuracy is critical)
                item.needs_review = True
                if not item.review_notes:
                    item.add_review_note("Extracted via OCR - Manual verification required")
                
                items.append(item)
                
                print(f"    Item {item.line_no}: {item.description[:40]}... (NSN: {item.nsn}, Qty: {item.qty})")
                print(f"      Confidence: {item.overall_confidence:.0f}% | Needs Review: {item.needs_review}")
    
    except Exception as e:
        print(f"\nERROR during OCR extraction: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*80}")
    print(f"EXTRACTION COMPLETE: {len(items)} items extracted")
    print(f"All items flagged for mandatory review")
    print(f"{'='*80}\n")
    
    return items


def generate_review_report(items: List[ExtractedItem]) -> str:
    """
    Generate a human-readable review report.
    
    This shows the user what was extracted and what needs verification.
    """
    report = []
    report.append("="*80)
    report.append("OCR EXTRACTION REVIEW REPORT")
    report.append("="*80)
    report.append(f"\nTotal Items Extracted: {len(items)}")
    report.append(f"Items Needing Review: {sum(1 for item in items if item.needs_review)}")
    
    # Overall statistics
    avg_confidence = sum(item.overall_confidence for item in items) / len(items) if items else 0
    report.append(f"Average Confidence: {avg_confidence:.1f}%")
    
    report.append(f"\n{'='*80}")
    report.append("ITEM-BY-ITEM REVIEW")
    report.append(f"{'='*80}\n")
    
    for item in items:
        report.append(f"Item #{item.line_no}:")
        report.append(f"  Description: {item.description}")
        report.append(f"  NSN: {item.nsn} (Confidence: {item.nsn_confidence:.0f}%)")
        report.append(f"  Quantity: {item.qty} (Confidence: {item.qty_confidence:.0f}%)")
        report.append(f"  Overall Confidence: {item.overall_confidence:.0f}%")
        
        if item.needs_review:
            report.append(f"  ⚠️  NEEDS REVIEW:")
            for note in item.review_notes:
                report.append(f"      - {note}")
        
        report.append("")
    
    report.append("="*80)
    report.append("INSTRUCTIONS:")
    report.append("1. Review each item carefully")
    report.append("2. Verify NSNs are correct (9 digits)")
    report.append("3. Check descriptions for OCR errors")
    report.append("4. Confirm quantities match source document")
    report.append("5. Make corrections in the preview interface")
    report.append("6. Only generate DD1750 after ALL items verified")
    report.append("="*80)
    
    return "\n".join(report)


# Test function
if __name__ == "__main__":
    # Test with handwritten BOM
    print("Testing OCR extraction...")
    
    test_pdf = "/mnt/user-data/uploads/handwritten_boms.pdf"
    items = extract_items_with_ocr(test_pdf)
    
    print("\n\n")
    report = generate_review_report(items)
    print(report)
    
    # Save report
    with open("/home/claude/ocr_review_report.txt", "w") as f:
        f.write(report)
    
    print("\n✅ Report saved to: /home/claude/ocr_review_report.txt")
