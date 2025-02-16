
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn, relationship
from sqlalchemy import ForeignKey, Table, String, Column,  Date
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
    order_date: Mapped[Date] = MappedColumn(Date)
    user_id: Mapped[int]= MappedColumn(ForeignKey("users.id"))
    
    
    #One-to-Many
    owners: Mapped[List["User"]] = relationship(back_populates="orders")

    #Many-to-Many
    ship_ready: Mapped[List["Product"]] = relationship(secondary= Order_Product , back_populates='shipments')
   

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = MappedColumn(Integer, primary_key = True)
    product_name: Mapped[str] = MappedColumn(String(200))
    price: Mapped[float] = MappedColumn(Float)

    #Many-to-Many
    shipments: Mapped[List["Order"]] = relationship(secondary= Order_Product, back_populates='ship_ready')
  

#------Schemas------

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User

class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        include_fk = True

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

#--------------------Product----------------------

#Create product
@app.route('/products', methods=['POST'])
def create_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_product = Product(product_name=product_data['product_name'], price=product_data['price'])
    db.session.add(new_product)
    db.session.commit()

    return product_schema.jsonify(new_product), 201

#Read all Product
@app.route('/products', methods=['GET'])
def get_products():
    query = Select(Product)
    products = db.session.execute(query).scalars().all()

    return products_schema.jsonify(products), 200

#Read a single product by ID
@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = db.session.get(Product, id)
    return product_schema.jsonify(product), 200

#Update User
@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = db.session.get(Product, id)

    if not product:
        return jsonify({"message": "Invalid product id"}), 400
    
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    product.product_name = product_data['product_name']
    product.price = product_data['price']
    

    db.session.commit()
    return product_schema.jsonify(product), 200

#Delete User
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = db.session.get(Product, id)

    if not product:
        return jsonify({"message": "Invalid product id"}), 400
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": f"succefully deleted product {id}"}), 200

#-------------------------Order---------------------------

#Create orders
@app.route('/orders',  methods=['POST'])
def create_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_order = Order(order_date = order_data['order_date'], user_id = order_data['user_id'])
    db.session.add(new_order)
    db.session.commit()

    return order_schema.jsonify(new_order), 201

#Add product to an order
@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['POST'])
def add_product(order_id, product_id):
    
    order = db.session.get(Order, order_id)
    product = db.session.get(Product, product_id)

    order.ship_ready.append(product)
    db.session.commit()
    return jsonify({"message": f"A shipment ordered {order.order_date} contains product(s){product.product_name}"}), 200





if __name__ == "__main__":

    with app.app_context():
        db.create_all()

        app.run(debug=True)