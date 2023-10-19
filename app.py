from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
from sqlalchemy import or_
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Kn5643121!@localhost/mydb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)


class Item(db.Model):
    __tablename__ = 'mydbtable'
    __table_args__ = {'schema': 'mydb'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)


@app.route('/')
def index():
    try:
        sort_by = request.args.get('sort_by', 'id_asc')

        if sort_by.startswith('id'):
            search_query = request.args.get('search', '')
            items = Item.query.filter(or_(Item.id.like(f'%{search_query}%'), Item.name.like(f'%{search_query}%')))
            items = items.order_by(Item.id.asc() if sort_by == 'id_asc' else Item.id.desc())
        elif sort_by.startswith('name'):
            items = Item.query.order_by(Item.name.asc() if sort_by == 'name_asc' else Item.name.desc())
        else:
            items = Item.query.order_by(Item.id)

        items = items.all()

        return render_template('Body.html', items=items, sort_by=sort_by)
    except Exception as e:
        return f"An error occurred: {str(e)}"


@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        image = save_uploaded_file(request.files['image'])

        # Find the smallest available ID with a gap
        available_ids = [id for id, in db.session.query(Item.id).order_by(Item.id)]
        new_id = find_smallest_gap(available_ids)

        new_item = Item(id=new_id, name=name, description=description, image=image)
        db.session.add(new_item)
        db.session.commit()

        # Redirect to the index page after adding an item
        return redirect(url_for('index'))

    return render_template('Border.html', action='add', item=None)


def find_smallest_gap(ids):
    """Find the smallest gap in a list of integers."""
    ids_set = set(ids)
    for i in range(1, len(ids) + 2):
        if i not in ids_set:
            return i
    return 1


@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit(item_id):
    item = Item.query.get(item_id)
    if request.method == 'POST':
        item.name = request.form['name']
        item.description = request.form['description']
        item.image = save_uploaded_file(request.files['image'])
        db.session.commit()

        # Redirect to the index page after editing an item
        return redirect(url_for('index'))

    return render_template('Border.html', action='edit', item=item, item_id=item_id)


@app.route('/delete/<int:item_id>', methods=['POST'])
def delete(item_id):
    try:
        item = Item.query.get(item_id)
        db.session.delete(item)
        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        return f"An error occurred: {str(e)}"


def save_uploaded_file(file):
    if file:
        try:
            # Open the uploaded image
            img = Image.open(file)

            # Resize the image to a suitable size (e.g., 300x300 pixels)
            img.thumbnail((300, 300))

            # Save the resized image
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            img.save(filename)

            return filename
        except Exception as e:
            print(f"An error occurred while processing the image: {str(e)}")
            return None
    return None


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
