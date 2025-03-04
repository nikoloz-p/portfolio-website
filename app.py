from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from forms import ProjectForm
from config import SECRET_KEY, ADMIN_PASSWORD
from werkzeug.utils import secure_filename
import os
from pathlib import Path

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["UPLOAD_FOLDER"] = "static/uploads"


db = SQLAlchemy(app)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255), nullable=False)
    width = db.Column(db.String(10), nullable=False)
    height = db.Column(db.String(10), nullable=False)
    grid_row = db.Column(db.String(50), nullable=False)
    grid_column = db.Column(db.String(50), nullable=False)
    show_on_works = db.Column(db.Boolean, nullable=False)
    sections = db.relationship('ProjectSection', backref='project', lazy=True, cascade="all, delete-orphan")

class ProjectSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'text' or 'image'
    content = db.Column(db.Text, nullable=True)  # Stores text or image URL
    order = db.Column(db.Integer, nullable=False)  # Order of sections

@app.route("/")
def home():
    projects = Project.query.all()  
    return render_template("index.html", projects=projects)

@app.route("/works")
def works():
    projects = Project.query.filter_by(show_on_works=True).all()
    return render_template("works.html", projects=projects)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "logged_in" not in session:  
        return redirect(url_for("admin_login"))
    
    form = ProjectForm()

    if form.validate_on_submit():
        image_path = form.image.data
        if image_path.startswith("static/"):
            image_path = image_path.replace("static/", "", 1)

        new_project = Project(
            title=form.title.data,
            image=image_path,  
            grid_row=form.grid_row.data,
            grid_column=form.grid_column.data,
            description=form.description.data,
            show_on_works=True
        )

        db.session.add(new_project)
        db.session.commit()
        return redirect(url_for("admin"))

    projects = Project.query.all()
    return render_template("admin.html", form=form, projects=projects)

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD: 
            session["logged_in"] = True  
            return redirect(url_for("admin"))
        else:
            return redirect(url_for("admin_login"))

    return '''
        <form method="POST">
            <label>Enter Admin Password:</label>
            <input type="password" name="password" required>
            <button type="submit">Login</button>
        </form>
        '''

@app.route("/admin-logout")
def admin_logout():
    session.pop("logged_in", None)  
    return redirect(url_for("admin_login"))

@app.route("/delete/<int:project_id>", methods=["POST"])
def delete_project(project_id):
    if "logged_in" not in session:  
        return redirect(url_for("admin_login"))

    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return redirect(url_for("admin"))

@app.route("/admin/project/<int:project_id>/edit", methods=["GET", "POST"])
def edit_project(project_id):
    if "logged_in" not in session:
        return redirect(url_for("admin_login"))

    project = Project.query.get_or_404(project_id)

    if request.method == "POST":
        # Update project details
        if "update_project" in request.form:
            project.title = request.form["title"]
            project.description = request.form["description"]

            # Handle main image upload
            if "main_image" in request.files:
                file = request.files["main_image"]
                if file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(file_path)
                    project.image = f"uploads/{filename}"

            db.session.commit()
            return redirect(url_for("edit_project", project_id=project.id))

        # Add new section (Text, Image, Image Row, Subtitle)
        elif "add_section" in request.form:
            section_type = request.form["type"]
            order = int(request.form["order"])

            if section_type == "text":
                content = request.form["content"]

            elif section_type == "image":
                file = request.files["image"]
                if file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(file_path)
                    content = f"uploads/{filename}"
                else:
                    content = None

            elif section_type == "image_row":
                files = request.files.getlist("image_row")
                image_paths = []
                for file in files:
                    if file.filename:
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                        file.save(file_path)
                        image_paths.append(f"uploads/{filename}")
                content = ",".join(image_paths)  # Store as comma-separated values

            elif section_type == "subtitle":
                content = request.form["content"]

            new_section = ProjectSection(
                project_id=project.id,
                type=section_type,
                content=content,
                order=order
            )
            db.session.add(new_section)
            db.session.commit()
            return redirect(url_for("edit_project", project_id=project.id))

    return render_template("admin_edit_project.html", project=project)

@app.route("/admin/project/<int:project_id>/delete_section/<int:section_id>", methods=["POST"])
def delete_section(project_id, section_id):
    if "logged_in" not in session:
        return redirect(url_for("admin_login"))

    section = ProjectSection.query.get_or_404(section_id)
    db.session.delete(section)
    db.session.commit()

    return redirect(url_for("edit_project", project_id=project_id))

# position projects

@app.route("/generate-css")
def generate_css():
    if "logged_in" not in session:
        return redirect(url_for("admin_login"))

    projects = Project.query.all()
    css_content = ""

    for project in projects:
        css_content += f"""
        .project-{project.id} {{
            grid-row: {project.grid_row if project.grid_row else "auto"};
            grid-column: {project.grid_column if project.grid_column else "auto"};
        }}
        .project-{project.id} .project_image-holder{{
            width: {project.width if project.width else "auto"}px;
            height: {project.height if project.height else "auto"}px;
        }}
        """

    with open("static/position_projects.css", "w") as css_file:
        css_file.write(css_content)


if __name__ == "__main__":
    app.run(debug=True)