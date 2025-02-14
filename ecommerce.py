from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn, relationship
from sqlalchemy import ForeignKey, Table, String, Column, DateTime
from typing import List

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import ForeignKey, Table, Column, String, Integer, Float, Select
from marshmallow import ValidationError
from typing import List, Optional


# Initialize Flask app
app = Flask(__name__)

# MySQL database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:80618StNE@localhost/ecommerce_api'

# Creating our Base Model
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy and Marshmallow
db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)

#-------Models----------

# Association Table 
Order_Product = Table(
    "order_product",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = MappedColumn(primary_key=True)
    name: Mapped[str] = MappedColumn(String(50))
    address: Mapped[str] = MappedColumn(String(200))
    email: Mapped[str] = MappedColumn(String(200), unique=True)
   
    
   #One-to-Many
    orders: Mapped[List["Order"]] = relationship( back_populates="owners")

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = MappedColumn(Integer, primary_key=True)
    order_date: Mapped[DateTime] = MappedColumn(DateTime)
    user_id: Mapped[int]= MappedColumn(ForeignKey("users.id"))
    
    
    #One-to-Many
    owners: Mapped[List["User"]] = relationship(back_populates="orders")

    #Many-to-Many
    ship_ready: Mapped[List["Order"]] = relationship(secondary= Order_Product)
   

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = MappedColumn(Integer, primary_key = True)
    product_name: Mapped[str] = MappedColumn(String(100))
    price: Mapped[float] = MappedColumn(Float)

    #Many-to-Many
    shipments: Mapped[List["Product"]] = relationship(secondary= Order_Product)
  

#------Schemas------

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User

class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product

user_schema = UserSchema()
users_schema = UserSchema(many=True) #Allows for the serialization of a list of user objects
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

#---------------Route----------------

#Create a User
@app.route('/users', methods=['POST'])
def create_user():
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_user = User(name=user_data['name'], address=user_data['address'], email=user_data['email'])
    db.session.add(new_user)
    db.session.commit()

    return user_schema.jsonify(new_user), 201

#Read User
@app.route('/users', methods=['GET'])
def get_users():
    query = Select(User)
    users = db.session.execute(query).scalars().all()

    return users_schema.jsonify(users), 200

#Read a single user by ID
@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = db.session.get(User, id)
    return user_schema.jsonify(user), 200

#Update User
@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = db.session.get(User, id)

    if not user:
        return jsonify({"message": "Invalid user id"}), 400
    
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    user.name = user_data['name']
    user.address = user_data['address']
    user.email = user_data['email']

    db.session.commit()
    return user_schema.jsonify(user), 200

#Delete User
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = db.session.get(User, id)

    if not user:
        return jsonify({"message": "Invalid user id"}), 400
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"succefully deleted user {id}"}), 200

#Create product
@app.route('/products', methods=['POST'])
def create_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_product = Product(name=product_data['product_name'], price=product_data['price'])
    db.session.add(new_product)
    db.session.commit()

    return product_schema.jsonify(new_product), 201

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

        app.run(debug=True)