#!/usr/bin/env python3
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Create upload directories if they don't exist
    upload_folders = ['app/static/uploads/profiles', 'app/static/uploads/posts', 'app/static/uploads/messages']
    for folder in upload_folders:
        os.makedirs(folder, exist_ok=True)

    app.run(debug=True, host='0.0.0.0', port=5000)
