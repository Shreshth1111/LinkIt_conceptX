#!/usr/bin/env python3
"""
Database setup script for LinkedIn Clone
Run this script to initialize the database with sample data
"""

from app import create_app, db
from app.models import User, Skill, Company, EducationalInstitution
from datetime import datetime
import os

def create_sample_data():
    """Create sample data for testing"""

    # Create sample skills
    skills_data = [
        ('Python', 'Programming'),
        ('JavaScript', 'Programming'),
        ('React', 'Frontend'),
        ('Flask', 'Backend'),
        ('MySQL', 'Database'),
        ('Project Management', 'Management'),
        ('Digital Marketing', 'Marketing'),
        ('Data Analysis', 'Analytics'),
        ('Machine Learning', 'AI/ML'),
        ('Communication', 'Soft Skills')
    ]

    for skill_name, category in skills_data:
        existing_skill = Skill.query.filter_by(skill_name=skill_name).first()
        if not existing_skill:
            skill = Skill(skill_name=skill_name, category=category)
            db.session.add(skill)

    # Create sample companies
    companies_data = [
        ('Tech Innovations Inc.', 'https://techinnovations.com', 'Technology', '201-500', 'San Francisco, CA'),
        ('Global Marketing Solutions', 'https://globalmarketing.com', 'Marketing & Advertising', '51-200', 'New York, NY'),
        ('DataFlow Analytics', 'https://dataflow.com', 'Data & Analytics', '11-50', 'Austin, TX'),
        ('Creative Designs Studio', 'https://creativedesigns.com', 'Design', '11-50', 'Los Angeles, CA'),
        ('FinTech Solutions', 'https://fintech.com', 'Financial Services', '101-200', 'Boston, MA')
    ]

    for name, website, industry, size, location in companies_data:
        existing_company = Company.query.filter_by(company_name=name).first()
        if not existing_company:
            company = Company(
                company_name=name,
                company_website=website,
                industry=industry,
                company_size=size,
                headquarters=location
            )
            db.session.add(company)

    # Create sample educational institutions
    institutions_data = [
        ('Stanford University', 'University', 'Stanford, CA'),
        ('MIT', 'University', 'Cambridge, MA'),
        ('Harvard University', 'University', 'Cambridge, MA'),
        ('UC Berkeley', 'University', 'Berkeley, CA'),
        ('New York University', 'University', 'New York, NY')
    ]

    for name, type_, location in institutions_data:
        existing_inst = EducationalInstitution.query.filter_by(institution_name=name).first()
        if not existing_inst:
            institution = EducationalInstitution(
                institution_name=name,
                institution_type=type_,
                location=location
            )
            db.session.add(institution)

    # Create admin user
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin = User(
            username='admin',
            email='admin@linkedinclone.com',
            first_name='Admin',
            last_name='User',
            headline='Platform Administrator',
            summary='Welcome to LinkedIn Clone! I am the administrator of this platform.',
            location='San Francisco, CA',
            industry='Technology',
            current_position='Platform Administrator',
            is_verified=True
        )
        admin.set_password('admin123')
        db.session.add(admin)

    db.session.commit()
    print("Sample data created successfully!")

def setup_database():
    """Initialize database and create sample data"""
    app = create_app()

    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()

        # Create upload directories
        upload_dirs = [
            'app/static/uploads/profiles',
            'app/static/uploads/posts/images',
            'app/static/uploads/posts/videos', 
            'app/static/uploads/posts/documents',
            'app/static/uploads/messages/images',
            'app/static/uploads/messages/files'
        ]

        for directory in upload_dirs:
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")

        # Create sample data
        create_sample_data()

        print("\nDatabase setup complete!")
        print("\nDefault admin account:")
        print("Username: admin")
        print("Password: admin123")
        print("\nYou can now run the application with: python run.py")

if __name__ == '__main__':
    setup_database()
