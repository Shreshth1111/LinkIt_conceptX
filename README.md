# LinkIt_conceptX
Concept X
# LinkedIn Clone - Full Stack Flask Application

A complete LinkedIn-style professional networking platform built with Flask, featuring user authentication, posts, connections, messaging, and more.

## Features

### Core Functionality
- **User Authentication**: Registration, login, logout with session management
- **Profile Management**: Complete user profiles with work experience, education, skills
- **Connection System**: Send/accept connection requests with friend recommendations  
- **Posts & Feed**: Create, edit, delete posts with images, videos, links, and documents
- **Real-time Messaging**: Private and group conversations with file sharing
- **Notifications**: Real-time notifications for all user activities

### Advanced Features
- **Friend Recommendations**: Algorithm-based connection suggestions
- **Search**: Search users, posts, and content across the platform
- **Privacy Controls**: Comprehensive privacy settings and user blocking
- **Skill Endorsements**: Professional skill management and peer endorsements
- **Activity Tracking**: User activity logging and analytics
- **Responsive Design**: Mobile-friendly Bootstrap interface

## Technology Stack

- **Backend**: Python 3.8+, Flask 3.0
- **Database**: MySQL with SQLAlchemy ORM
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Authentication**: Flask-Login with session management
- **Forms**: Flask-WTF with validation
- **File Uploads**: Werkzeug secure file handling
- **Database Migrations**: Flask-Migrate

## Prerequisites

Before running this application, make sure you have:

1. **Python 3.8 or higher** installed
2. **MySQL Server** running (XAMPP recommended for local development)
3. **Git** (optional, for version control)

## Installation & Setup

### Step 1: Extract and Navigate
1. Extract the downloaded ZIP file to your desired location
2. Open a terminal/command prompt and navigate to the project directory:
   ```bash
   cd linkedin-clone-flask
   ```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Database

#### Option A: Using XAMPP (Recommended)
1. Start XAMPP and ensure MySQL is running
2. Open phpMyAdmin (http://localhost/phpmyadmin)
3. Create a new database named `linkedin_clone`
4. Import the provided `linkedin_database_schema.sql` file OR let the application create tables automatically

#### Option B: Using MySQL Command Line
```bash
mysql -u root -p
CREATE DATABASE linkedin_clone CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit;
```

### Step 5: Configure Environment Variables
1. Copy the `.env` file and update the database connection:
   ```env
   # Database Configuration
   DATABASE_URI=mysql://root:YOUR_PASSWORD@localhost/linkedin_clone

   # Change this to a secure secret key
   SECRET_KEY=your-super-secret-key-change-this-in-production
   ```

### Step 6: Initialize Database
```bash
python setup_db.py
```

This will:
- Create all database tables
- Create necessary upload directories
- Insert sample data (skills, companies, educational institutions)
- Create an admin user account

### Step 7: Run the Application
```bash
python run.py
```

The application will be available at: **http://localhost:5000**

## Default Admin Account

After running `setup_db.py`, you can login with:
- **Username**: `admin`
- **Password**: `admin123`

## Project Structure

```
linkedin-clone-flask/
├── app/
│   ├── __init__.py              # Flask application factory
│   ├── models.py                # Database models
│   ├── forms.py                 # WTForms form classes
│   ├── auth/                    # Authentication blueprint
│   ├── main/                    # Main application routes
│   ├── posts/                   # Posts functionality
│   ├── connections/             # Connection management
│   ├── messages/                # Messaging system
│   ├── profile/                 # Profile management
│   ├── templates/               # HTML templates
│   └── static/                  # Static files (CSS, JS, uploads)
├── config.py                    # Configuration settings
├── run.py                      # Application entry point
├── setup_db.py                 # Database initialization script
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── README.md                   # This file
```

## Database Schema

The application uses a comprehensive database schema with 20+ tables:

### Core Tables
- `users` - User accounts and profiles
- `posts` - User posts and content
- `connections` - User connections and friend requests
- `messages` - Messaging system
- `notifications` - User notifications

### Profile Tables
- `work_experiences` - Professional experience
- `education` - Educational background
- `skills` - User skills and endorsements
- `companies` - Company information

### Activity Tables
- `post_reactions` - Post likes and reactions
- `comments` - Post comments and replies
- `post_shares` - Shared posts

## Key Features Guide

### 1. User Registration & Authentication
- Navigate to `/auth/register` to create a new account
- Login at `/auth/login`
- Profile management at `/profile/edit`

### 2. Creating Posts
- Click "Start a post..." on the homepage
- Support for text, images, videos, links, and documents
- Privacy controls (Public, Connections Only, Private)

### 3. Building Your Network
- Visit "My Network" to see connection requests
- Use "People You May Know" for suggestions
- Search for users and send connection requests

### 4. Messaging
- Access messages through the envelope icon in navigation
- Start new conversations with connections
- Support for text messages and file attachments

### 5. Profile Management
- Add work experience and education
- Upload profile and cover photos
- Manage skills and get endorsements

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/logout` - User logout

### Posts
- `GET /posts/create` - Create new post
- `POST /api/react_post/<id>` - React to post
- `POST /posts/post/<id>/share` - Share post

### Connections
- `POST /connections/send_request/<user_id>` - Send connection request
- `GET /connections/respond_request/<id>/<action>` - Accept/reject request

### Messages
- `POST /messages/send_message` - Send message
- `POST /api/send_quick_message` - Quick AJAX message

## Customization

### Styling
- Modify `app/templates/base.html` for global styling
- Custom CSS is included in the base template
- Bootstrap classes can be customized

### Adding Features
1. Create new blueprints in the `app/` directory
2. Add routes and templates
3. Register the blueprint in `app/__init__.py`

### Database Changes
1. Modify models in `app/models.py`
2. Create migration: `flask db migrate -m "Description"`
3. Apply migration: `flask db upgrade`

## Production Deployment

### Environment Variables
Set these environment variables for production:
```env
FLASK_ENV=production
SECRET_KEY=your-production-secret-key
DATABASE_URI=your-production-database-url
```

### Security Considerations
1. Change the default secret key
2. Use HTTPS in production
3. Configure proper database credentials
4. Set up file upload limits
5. Implement rate limiting
6. Use a reverse proxy (Nginx)

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure MySQL is running
   - Check database credentials in `.env`
   - Verify database `linkedin_clone` exists

2. **Import Errors** 
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

3. **File Upload Issues**
   - Check upload directory permissions
   - Verify `UPLOAD_FOLDER` configuration

4. **Template Not Found**
   - Ensure all template files are in place
   - Check template paths in routes

### Debug Mode
Set `FLASK_ENV=development` in `.env` to enable debug mode with detailed error messages.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

For support and questions:
- Check the troubleshooting section above
- Review the code comments for implementation details
- Create an issue in the project repository

---

**Note**: This is a demo application for educational purposes. For production use, implement additional security measures, testing, and monitoring.
