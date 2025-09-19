from flask import Flask, render_template, request, url_for, redirect, Response, send_from_directory
import pandas as pd
import os, uuid

app = Flask(__name__, template_folder = 'templates')

@app.route('/', methods = ['GET', 'POST'])
def index():
  if request.method == 'GET':
    return render_template("index.html")
  elif request.method == 'POST':
    username = request.form.get('username')
    password = request.form.get('password')

    if username == 'om' and password == '123':
      return "Success"
    else:
      return "Faliure"
    
@app.route('/file_upload', methods = ['POST'])
def file_upload():
  file = request.files['file']
  if file.content_type == 'text/plain':
    return file.read().decode()
  elif file.content_type == 'application/vnd.ms-excel' or file.content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
    df = pd.read_excel(file)
    return df.to_html()
  
@app.route('/convert_csv', methods = ['GET', 'POST'])
def convert():
  file = request.files['file']

  df = pd.read_excel(file)

  response = Response(
    df.to_csv(), 
    mimetype = 'text/csv', # MIME type means content type.
    headers = {
      'Content-Disposition': 'attachment; filename = result.csv'      
    }
  )
  return response

## This above method is of direct download of the file.
## Now we will see the method which will redirect to the download page and the user will click the download button for the download of file.

@app.route('/convert2', methods=['POST'])
def convert_csv_two():
    file = request.files['file']
    df = pd.read_excel(file)
    
    # Create downloads directory if it doesn't exist
    downloads_dir = os.path.join(app.root_path, 'downloads')
    if not os.path.exists(downloads_dir):
        os.makedirs(downloads_dir)
        print(f'[DEBUG] Created downloads directory: {downloads_dir}')
    
    filename = f'{uuid.uuid4()}.csv'
    file_path = os.path.join(downloads_dir, filename)
    
    # Save the file
    df.to_csv(file_path, index=False)
    
    # Debug information
    print(f'[DEBUG] Saved file to: {file_path}')
    print(f'[DEBUG] File exists after save: {os.path.exists(file_path)}')
    print(f'[DEBUG] File size: {os.path.getsize(file_path) if os.path.exists(file_path) else "File not found"}')
    print(f'[DEBUG] Generated filename: {filename}')
    
    return render_template('download.html', filename=filename)


@app.route('/download/<filename>')
def download(filename):
    try:
        # Use absolute path to be sure
        downloads_path = 'downloads'  # Relative to where you run the app
        return send_from_directory(
            downloads_path, 
            filename, 
            as_attachment=True,
            download_name="result.csv"
        )
    except FileNotFoundError:
        return "File not found", 404
    except Exception as e:
        return f"Error downloading file: {str(e)}", 500


if __name__ == "__main__":
  app.run(debug = True)