# Image Host - Django Image Management System

A simple Django-based image hosting system that allows users to organize images by projects, with auto-generated image codes and publicly accessible URLs.

## Features

- **User Authentication**: Simple user registration and login system
- **Project Management**: Organize images into projects
- **Image Upload**: Upload multiple images per project
- **Auto-generated Image Codes**: Automatically generates lowercase, underscore-separated codes from image filenames
- **Editable Image Codes**: Edit image codes after upload
- **Public URLs**: Each image gets a publicly accessible URL using its image code
- **Image Display**: View all images in a project with name, code, and URL

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create a Superuser (Optional)

```bash
python manage.py createsuperuser
```

This allows you to access the Django admin panel at `/admin/`.

### 4. Run the Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Usage

1. **Register/Login**: Create an account or login with existing credentials
2. **Create a Project**: Click "Create New Project" and enter a project name
3. **Upload Images**: 
   - Enter an image name
   - Select an image file
   - The image code will be auto-generated from the filename (editable)
   - Click "Upload Image"
4. **Edit Images**: 
   - Click on the image name or code to edit them inline
   - Click "Save" to update
5. **View URLs**: Each image has a publicly accessible URL that you can copy

## Project Structure

```
imagehost/
├── imagehost/          # Main Django project settings
├── images/             # Images app
│   ├── models.py       # Project and Image models
│   ├── views.py        # View functions
│   ├── forms.py        # Django forms
│   ├── urls.py         # URL routing
│   └── templates/      # HTML templates
├── media/              # Uploaded images (created automatically)
├── db.sqlite3          # SQLite database (created after migrations)
└── manage.py           # Django management script
```

## Database

The project uses SQLite (default Django database) for easy setup. The database file `db.sqlite3` will be created automatically after running migrations.

## Image Code Format

Image codes are automatically generated from filenames:
- Converted to lowercase
- Special characters removed
- Spaces replaced with underscores
- Multiple underscores collapsed to single underscore
- Example: "My Image File.jpg" → "my_image_file"

## Public Image URLs

Images are accessible via:
```
http://your-domain/image/<image_code>/
```

For example, if your image code is `my_image_file`, the URL would be:
```
http://127.0.0.1:8000/image/my_image_file/
```