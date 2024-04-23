from flask import Flask, jsonify, render_template, request
from neo4j import GraphDatabase

app = Flask(__name__)
app.template_folder = "Template"
app.static_folder = "Static"

uri = "bolt://localhost:7687"
username = "neo4j"
password = "password"

driver = GraphDatabase.driver(uri, auth=(username, password))


def get_customers_from_neo4j():
    with driver.session() as session:
        result = session.run("MATCH (c:Customer) RETURN c")
        customers = [record["c"] for record in result]
    return customers

def search_customers(search_input):
    with driver.session() as session:
        result = session.run("MATCH (c:Customer) WHERE c.companyName CONTAINS $search_input OR c.contactName CONTAINS $search_input OR c.address CONTAINS $search_input RETURN c",
                             search_input=search_input)
        customers = [dict(record["c"]) for record in result]
    return customers

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_input = request.form['search_input']
        customers = search_customers(search_input)
        return render_template('customers.html', customers=customers)
    else:
        return render_template('search.html')

@app.route('/')
def index():
    try:
        with driver.session() as session:
            session.run("RETURN 1")
        return ("Hello Neo4j!")
    except Exception as e:
        return (f"Error: {str(e)}")


@app.route('/customers')
def show_customers():
    customers = get_customers_from_neo4j()
    return render_template('customers.html', customers=customers)


@app.route('/test')
def test():
    #Tạo session và chạy lệnh truy vấn, gán kết quả vào biến result
    session = driver.session()
    result = session.run("MATCH (c:Customer) RETURN c.contactName AS contact_name")

    #Đọc bản ghi và trích xuất dữ liệu
    customer_names = [record["contact_name"] for record in result]

    #Đóng session và driver
    session.close()
    driver.close()

    #Trả kết quả về JSON
    return jsonify(customer_names)

@app.route('/delete')
def selectName():
    return render_template('delete.html')

@app.route('/deleteCustomer', methods=['POST'])
def delete_customer():
    name = request.form['name']
    with driver.session() as session:
        session.run("MATCH (c:Customer)-[rel]-(n) WHERE c.contactName = $name DELETE rel", name=name)
        session.run("MATCH (c:Customer) WHERE c.contactName = $name DELETE c", name=name)


    driver.close()
    return jsonify({"message": f"Customer {name} has been deleted."})

@app.route('/add')
def fill_info():
    return render_template('add.html')

@app.route('/addCustomer', methods=['POST'])
def add_customer():
    contact_name = request.form.get('contactName')
    address = request.form.get('address')
    phone = request.form.get('phone')
    company_name = request.form.get('companyName')

    with driver.session() as session:
        result = session.run("MERGE (c:Customer {contactName: $contactName}) "
                    "ON CREATE SET c.address = $address, c.phone = $phone, c.companyName = $companyName "
                    "RETURN c",
                    contactName=contact_name, address=address, phone=phone, companyName=company_name)
        customer = [record["c"] for record in result]

    return render_template('customers.html', customers=customer)


@app.route('/update/<contact_name>', methods=['GET'])
def update_customer(contact_name):
    return render_template('edit.html', customer=contact_name)

@app.route('/updateCustomer', methods=['POST'])
def update_customer_info():
    old_name = request.form['oldName']
    contact_name = request.form['contactName']
    address = request.form['address']
    phone = request.form['phone']
    company_name = request.form['companyName']

    with driver.session() as session:
        result = session.run("MERGE (c:Customer {contactName: $oldName}) "
                    "ON MATCH SET c.contactName = $contactName, c.address = $address, c.phone = $phone, c.companyName = $companyName "
                    "RETURN c",
                    oldName=old_name, contactName=contact_name, address=address, phone=phone, companyName=company_name)
        customer = [record["c"] for record in result]

    return render_template('customers.html', customers=customer)


if __name__ == '__main__':
    app.run(debug=True)