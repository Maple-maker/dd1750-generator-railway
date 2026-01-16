"""
Enhanced DD1750 Generator with OCR and Preview
Accuracy-First Design: Mandatory human verification before DD1750 generation
"""

import os
import tempfile
import json
from flask import Flask, render_template, request, send_file, jsonify, session
from werkzeug.utils import secure_filename
from dd1750_ocr import extract_items_with_ocr, generate_review_report, ExtractedItem
from dd1750_core import generate_dd1750_from_verified_items, detect_bom_format
from dataclasses import asdict

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index_with_preview.html')


@app.route('/upload', methods=['POST'])
def upload():
    """
    Handle PDF upload and extract items for preview.
    """
    try:
        # Check files
        if 'bom_file' not in request.files or 'template_file' not in request.files:
            return jsonify({'error': 'Missing required files'}), 400
        
        bom_file = request.files['bom_file']
        template_file = request.files['template_file']
        
        if bom_file.filename == '' or template_file.filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        if not (allowed_file(bom_file.filename) and allowed_file(template_file.filename)):
            return jsonify({'error': 'Only PDF files allowed'}), 400
        
        # Save files temporarily
        with tempfile.TemporaryDirectory() as tmpdir:
            bom_path = os.path.join(tmpdir, secure_filename(bom_file.filename))
            template_path = os.path.join(tmpdir, secure_filename(template_file.filename))
            
            bom_file.save(bom_path)
            template_file.save(template_path)
            
            # Get start page
            start_page = int(request.form.get('start_page', 0))
            
            # Detect format
            bom_format = detect_bom_format(bom_path)
            print(f"Detected BOM format: {bom_format}")
            
            # Extract items based on format
            if bom_format in ['HANDWRITTEN_OCR', 'UNKNOWN']:
                print("Using OCR extraction...")
                items = extract_items_with_ocr(bom_path, start_page)
            else:
                print("Using text-based extraction...")
                # For now, use OCR for everything to be safe
                items = extract_items_with_ocr(bom_path, start_page)
            
            # Store items in session
            session['items'] = [asdict(item) for item in items]
            session['template_path'] = template_path  # Store for later use
            
            # Generate review report
            report = generate_review_report(items)
            
            # Return items for preview
            return jsonify({
                'success': True,
                'format': bom_format,
                'total_items': len(items),
                'items': [asdict(item) for item in items],
                'report': report,
                'needs_review': all(item.needs_review for item in items)
            })
    
    except Exception as e:
        print(f"Error during upload: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/update_items', methods=['POST'])
def update_items():
    """
    Update items with user corrections.
    """
    try:
        updated_items = request.json.get('items', [])
        session['items'] = updated_items
        
        return jsonify({'success': True, 'message': 'Items updated successfully'})
    
    except Exception as e:
        print(f"Error updating items: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/generate', methods=['POST'])
def generate():
    """
    Generate DD1750 from verified items.
    """
    try:
        # Get verified items from session
        items_data = session.get('items', [])
        
        if not items_data:
            return jsonify({'error': 'No items found. Please upload a BOM first.'}), 400
        
        # Convert back to ExtractedItem objects
        items = []
        for item_dict in items_data:
            item = ExtractedItem(
                line_no=item_dict['line_no'],
                description=item_dict['description'],
                nsn=item_dict['nsn'],
                qty=item_dict['qty'],
                description_confidence=item_dict.get('description_confidence', 100.0),
                nsn_confidence=item_dict.get('nsn_confidence', 100.0),
                qty_confidence=item_dict.get('qty_confidence', 100.0),
                needs_review=item_dict.get('needs_review', False),
                review_notes=item_dict.get('review_notes', [])
            )
            items.append(item)
        
        # Check if any items still need review
        if any(item.needs_review for item in items):
            needs_review_count = sum(1 for item in items if item.needs_review)
            return jsonify({
                'error': f'{needs_review_count} items still need review. Please verify all items before generating DD1750.'
            }), 400
        
        # Generate DD1750
        with tempfile.TemporaryDirectory() as tmpdir:
            # Get template (in real app, this should be persisted properly)
            template_path = '/mnt/project/blank_1750.pdf'  # Default template
            output_path = os.path.join(tmpdir, 'DD1750_generated.pdf')
            
            # Use the improved generator (we'll need to adapt it to work with ExtractedItem)
            # For now, let's create a simple generator
            from dd1750_core_improved import (
                PdfReader, PdfWriter, canvas, io, math,
                ROWS_PER_PAGE, PAGE_W, PAGE_H,
                X_BOX_L, X_BOX_R, X_CONTENT_L, X_CONTENT_R,
                X_UOI_L, X_UOI_R, X_INIT_L, X_INIT_R,
                X_SPARES_L, X_SPARES_R, X_TOTAL_L, X_TOTAL_R,
                Y_TABLE_TOP_LINE, PAD_X, ROW_H
            )
            
            total_pages = math.ceil(len(items) / ROWS_PER_PAGE)
            writer = PdfWriter()
            
            for page_num in range(total_pages):
                start_idx = page_num * ROWS_PER_PAGE
                end_idx = min((page_num + 1) * ROWS_PER_PAGE, len(items))
                page_items = items[start_idx:end_idx]
                
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=(PAGE_W, PAGE_H))
                
                first_row_top = Y_TABLE_TOP_LINE - 5.0
                
                for i, item in enumerate(page_items):
                    y = first_row_top - (i * ROW_H)
                    y_desc = y - 7.0
                    y_nsn = y - 12.2
                    
                    can.setFont("Helvetica", 8)
                    can.drawCentredString((X_BOX_L + X_BOX_R)/2, y_desc, str(item.line_no))
                    
                    can.setFont("Helvetica", 7)
                    desc = item.description[:50] if len(item.description) > 50 else item.description
                    can.drawString(X_CONTENT_L + PAD_X, y_desc, desc)
                    
                    if item.nsn:
                        can.setFont("Helvetica", 6)
                        can.drawString(X_CONTENT_L + PAD_X, y_nsn, f"NSN: {item.nsn}")
                    
                    can.setFont("Helvetica", 8)
                    can.drawCentredString((X_UOI_L + X_UOI_R)/2, y_desc, "EA")
                    can.drawCentredString((X_INIT_L + X_INIT_R)/2, y_desc, str(item.qty))
                    can.drawCentredString((X_SPARES_L + X_SPARES_R)/2, y_desc, "0")
                    can.drawCentredString((X_TOTAL_L + X_TOTAL_R)/2, y_desc, str(item.qty))
                
                can.save()
                packet.seek(0)
                
                overlay = PdfReader(packet)
                page = PdfReader(template_path).pages[0]
                page.merge_page(overlay.pages[0])
                writer.add_page(page)
            
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            return send_file(output_path, as_attachment=True, download_name='DD1750.pdf')
    
    except Exception as e:
        print(f"Error generating DD1750: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
