# app.py
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
import logging
import os

# Import our modules
import config
from utils.pdf_utils import extract_text_from_pdf, extract_tables_from_pdf, validation_pdf
from utils.data_io import save_both, DataIO
from parsers.bank_detector import detect_bank, detect_bank_with_confidence
from parsers import AxisParser, CitiParser, HdfcParser, IciciParser, SilkParser

# Setup logging
logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE * config.MAX_FILES  # Total upload size
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = config.OUTPUT_FOLDER

# Bank parser mapping
BANK_PARSERS = {
    'axis': AxisParser(),
    'citi': CitiParser(),
    'hdfc': HdfcParser(),
    'icici': IciciParser(),
    'silk': SilkParser(),
}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


def cleanup_uploads():
    """Clean up uploaded files from uploads folder."""
    try:
        upload_folder = Path(config.UPLOAD_FOLDER)
        if upload_folder.exists():
            for file in upload_folder.glob('*.pdf'):
                file.unlink()
            logger.info("Cleaned up uploaded files")
    except Exception as e:
        logger.error(f"Error cleaning up uploads: {str(e)}")


@app.route('/')
def index():
    """Render the main page."""
    return render_template('home.html')


@app.route('/upload', methods=['POST'])
def upload_files():
    """
    Handle multiple PDF uploads and parse them.
    
    Expected: Multiple files with key 'files[]'
    Returns: JSON with parsed results
    """
    logger.info("Received upload request")
    
    # Check if files are present
    if 'files[]' not in request.files:
        logger.warning("No files in request")
        return jsonify({
            'success': False,
            'error': 'No files uploaded'
        }), 400
    
    files = request.files.getlist('files[]')
    
    # Validate file count
    if len(files) == 0:
        return jsonify({
            'success': False,
            'error': 'No files selected'
        }), 400
    
    if len(files) > config.MAX_FILES:
        return jsonify({
            'success': False,
            'error': f'Maximum {config.MAX_FILES} files allowed'
        }), 400
    
    # Clean up previous uploads
    cleanup_uploads()
    
    # Process each file
    results = []
    saved_files = []
    
    for file in files:
        if file.filename == '':
            continue
        
        if not allowed_file(file.filename):
            results.append({
                'filename': file.filename,
                'status': 'error',
                'error': 'Invalid file type. Only PDF files allowed.'
            })
            continue
        
        try:
            # Save uploaded file
            filename = secure_filename(file.filename)
            filepath = config.UPLOAD_FOLDER / filename
            file.save(str(filepath))
            saved_files.append(filepath)
            
            logger.info(f"Processing file: {filename}")
            
            # Validate PDF
            is_valid, validation_msg = validation_pdf(str(filepath))
            if not is_valid:
                results.append({
                    'filename': filename,
                    'status': 'error',
                    'error': f'Invalid PDF: {validation_msg}'
                })
                continue
            
            # Extract text and tables
            text, extraction_method = extract_text_from_pdf(str(filepath))
            tables = extract_tables_from_pdf(str(filepath))
            
            if not text:
                results.append({
                    'filename': filename,
                    'status': 'error',
                    'error': 'Could not extract text from PDF'
                })
                continue
            
            logger.info(f"Text extracted using: {extraction_method}")
            logger.info(f"Found {len(tables)} tables")
            
            # Detect bank
            detected_bank = detect_bank(text)
            
            if not detected_bank:
                results.append({
                    'filename': filename,
                    'status': 'error',
                    'error': 'Could not identify bank from statement'
                })
                continue
            
            logger.info(f"Detected bank: {detected_bank.upper()}")
            
            # Get appropriate parser
            parser = BANK_PARSERS.get(detected_bank)
            
            if not parser:
                results.append({
                    'filename': filename,
                    'status': 'error',
                    'error': f'No parser available for bank: {detected_bank}'
                })
                continue
            
            # Parse the statement
            parsed_data = parser.extract_data(text, filename=filename, tables=tables)
            results.append(parsed_data)
            
            logger.info(f"Successfully parsed {filename}: {parsed_data.get('status')}")
        
        except Exception as e:
            logger.error(f"Error processing {file.filename}: {str(e)}")
            results.append({
                'filename': file.filename,
                'status': 'error',
                'error': f'Processing error: {str(e)}'
            })
    
    # Save results to JSON and CSV
    if results:
        try:
            save_results = save_both(results)
            json_success = save_results['json'][0]
            csv_success = save_results['csv'][0]
            
            if json_success and csv_success:
                logger.info("Successfully saved results to JSON and CSV")
            else:
                logger.warning("Failed to save some output files")
        
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
    
    # Generate summary
    summary = DataIO.export_summary(results)
    
    # Clean up uploaded files
    cleanup_uploads()
    
    # Return response
    return jsonify({
        'success': True,
        'results': results,
        'summary': summary
    })


@app.route('/download/<file_type>')
def download_file(file_type):
    """
    Download parsed results.
    
    Args:
        file_type: 'json' or 'csv'
    """
    try:
        if file_type == 'json':
            file_path = config.JSON_OUTPUT
            mimetype = 'application/json'
        elif file_type == 'csv':
            file_path = config.CSV_OUTPUT
            mimetype = 'text/csv'
        else:
            return jsonify({'error': 'Invalid file type'}), 400
        
        if not file_path.exists():
            return jsonify({'error': f'{file_type.upper()} file not found'}), 404
        
        logger.info(f"Sending {file_type.upper()} file for download")
        
        return send_file(
            file_path,
            mimetype=mimetype,
            as_attachment=True,
            download_name=file_path.name
        )
    
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'supported_banks': config.SUPPORTED_BANKS,
        'max_files': config.MAX_FILES
    })


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size: {config.MAX_FILE_SIZE / (1024*1024):.0f}MB'
    }), 413


@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error. Please try again.'
    }), 500


if __name__ == '__main__':
    # Create necessary directories
    config.UPLOAD_FOLDER.mkdir(exist_ok=True)
    config.OUTPUT_FOLDER.mkdir(exist_ok=True)
    
    # Run the app
    logger.info("Starting Flask application...")
    logger.info(f"Supported banks: {', '.join(config.SUPPORTED_BANKS)}")
    logger.info(f"Max files per upload: {config.MAX_FILES}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)