"""
Enhanced DD1750 Generator with OCR and Preview
Railway Deployment Ready
"""

import os
import tempfile
import json
from flask import Flask, render_template, request, send_file, jsonify, session
from werkzeug.utils import secure_filename
from dd1750_ocr import extract_items_with_ocr, generate_review_report, ExtractedItem
from dd1750_core import generate_dd1750_from_verified_items, detect_bom_format
from dataclasses import asdict
import base64

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production-railway')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint for Railway"""
    return jsonify({'status': 'healthy', 'service': 'dd1750-generator'}), 200


@app.route('/upload', methods=['POST'])
def upload():
    """Handle PDF upload and extract items for preview"""
    try:
        print("=== UPLOAD REQUEST RECEIVED ===")
        
        # Check files
        if 'bom_file' not in request.files or 'template_file' not in request.files:
            print("ERROR: Missing files in request")
            return jsonify({'error': 'Missing required files'}), 400
        
        bom_file = request.files['bom_file']
        template_file = request.files['template_file']
        
        print(f"BOM file: {bom_file.filename}")
        print(f"Template file: {template_file.filename}")
        
        if bom_file.filename == '' or template_file.filename == '':
            print("ERROR: Empty filename")
            return jsonify({'error': 'No files selected'}), 400
        
        if not (allowed_file(bom_file.filename) and allowed_file(template_file.filename)):
            print("ERROR: Invalid file type")
            return jsonify({'error': 'Only PDF files allowed'}), 400
        
        # Save files temporarily
        with tempfile.TemporaryDirectory() as tmpdir:
            bom_path = os.path.join(tmpdir, secure_filename(bom_file.filename))
            template_path = os.path.join(tmpdir, secure_filename(template_file.filename))
            
            bom_file.save(bom_path)
            template_file.save(template_path)
            
            print(f"Files saved to: {tmpdir}")
            
            # Store template in session for later use
            with open(template_path, 'rb') as f:
                template_b64 = base64.b64encode(f.read()).decode('utf-8')
                session['template_b64'] = template_b64
            
            print("Template stored in session")
            
            # Get start page
            start_page = int(request.form.get('start_page', 0))
            print(f"Start page: {start_page}")
            
            # Detect format
            print("Detecting BOM format...")
            bom_format = detect_bom_format(bom_path)
            print(f"Detected BOM format: {bom_format}")
            
            # Extract items using OCR
            print("Starting OCR extraction...")
            items = extract_items_with_ocr(bom_path, start_page)
            print(f"Extracted {len(items)} items")
            
            # Store items in session
            items_list = [asdict(item) for item in items]
            session['items'] = items_list
            print(f"Items stored in session: {len(items_list)}")
            
            # Generate review report
            report = generate_review_report(items)
            
            # Return items for preview
            response_data = {
                'success': True,
                'format': bom_format,
                'total_items': len(items),
                'items': items_list,
                'report': report,
                'needs_review': all(item.needs_review for item in items)
            }
            
            print(f"Returning response with {len(items_list)} items")
            return jsonify(response_data)
    
    except Exception as e:
        print(f"=== ERROR during upload ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/update_items', methods=['POST'])
def update_items():
    """Update items with user corrections"""
    try:
        updated_items = request.json.get('items', [])
        session['items'] = updated_items
        
        return jsonify({'success': True, 'message': 'Items updated successfully'})
    
    except Exception as e:
        print(f"Error updating items: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/generate', methods=['POST'])
def generate():
    """Generate DD1750 from verified items"""
    try:
        # Get verified items from session
        items_data = session.get('items', [])
        template_b64 = session.get('template_b64')
        
        if not items_data:
            return jsonify({'error': 'No items found. Please upload a BOM first.'}), 400
        
        if not template_b64:
            return jsonify({'error': 'Template not found. Please upload files again.'}), 400
        
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
            # Restore template from base64
            template_path = os.path.join(tmpdir, 'template.pdf')
            with open(template_path, 'wb') as f:
                f.write(base64.b64decode(template_b64))
            
            output_path = os.path.join(tmpdir, 'DD1750_generated.pdf')
            
            # Generate the DD1750
            generate_dd1750_from_verified_items(items, template_path, output_path)
            
            return send_file(output_path, as_attachment=True, download_name='DD1750.pdf')
    
    except Exception as e:
        print(f"Error generating DD1750: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
