##
## =============================================
## ============== Bases de Dados ===============
## ============== LEI  2021/2022 ===============
## =============================================
## =============================================
## =============================================
## =============================================
## === Department of Informatics Engineering ===
## =========== University of Coimbra ===========
## =============================================
##
 

import flask
import logging, psycopg2, time
import jwt
from functools import wraps
from datetime import datetime, timedelta, timezone

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'verysecretkey'

StatusCodes = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500
}

#########################################################
## TOKEN REQUIRED
#########################################################

def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in flask.request.headers:
            token = flask.request.headers['x-access-token']

        if not token:
            return flask.jsonify({"alerta": "Missing Token!"}), 400
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            user_id = data['user_id']
        except:
            return flask.jsonify({'alerta': 'Invalid Token!'}), 400
        return func(user_id,*args, **kwargs)
    return decorated

##########################################################
## DATABASE ACCESS
##########################################################

def db_connection():
    db = psycopg2.connect(
        user = "postgres",
        password = "postgres",
        host = 'dbproject',
        port = "5432",
        database = "dbproj"
    )
    
    return db

##########################################################
## ENDPOINTS
##########################################################


@app.route('/')
def landing_page():
    return """
    Hello World (Python)!  <br/>
    <br/>
    Check the sources for instructions on how to use the endpoints!<br/>
    <br/>
    Equipa de dev Luís Vieira , Eduardo e Raul Sofia<br/>
    <br/>
    """
    

@app.route('/dbproj/user', methods=['POST'])
def add_user():
    logger.info('POST /dbproj/user')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /dbproj/user - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    
    if 'name' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'name value not in payload'}
        return flask.jsonify(response)
    
    # parameterized queries, good for security and performance
    statement = 'INSERT INTO utilizador (name, email, pass, admin) VALUES (%s, %s, %s, %s)'
    values = (payload['name'], payload['email'], payload['pass'], payload['admin'])

    try:
        cur.execute(statement, values)

        # commit the transaction
        conn.commit()
        response = {'status': StatusCodes['success'], 'results': f'Inserted utilizador {payload["name"]}'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/user - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


@app.route('/dbproj/user', methods=['PUT'])
def login_user():
    logger.info('PUT /dbproj/user')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()
    
    logger.debug(f'PUT /dbproj/user - payload: {payload}')

    try:
        # parameterized queries, good for security and performance
        cur.execute('SELECT name,pass,id FROM utilizador WHERE name = %s',(payload['name'],))
        rows = cur.fetchall()

        row = rows[0]
        
        if (payload['pass'] == row[1]):
            utc_dt_aware = datetime.now(timezone.utc)
            token = jwt.encode({
                'user_id': row[2],
                'exp': utc_dt_aware + timedelta(minutes = 120)
            },
                app.config['SECRET_KEY'])
            response = {'status': StatusCodes['success'], 'results': f'Inserted user {payload["name"]}'}
            return flask.jsonify({'token': token.decode('utf-8')})
        else:
            response = {'status': StatusCodes['api_error'], 'results': f'Incorrect password'}
            return flask.jsonify(response)
        

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'PUT /dbproj/user - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

    finally:
        if conn is not None:
            conn.close()
    
    return flask.jsonify(response)



@app.route('/dbproj/product', methods=['POST'])
@token_required
def add_product(user_id):
    logger.info('POST /dbproj/product')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /dbproj/product - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    
    if 'name' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'name value not in payload'}
        return flask.jsonify(response)
    
    # parameterized queries, good for security and performance
    statement = 'INSERT INTO product (name, stock, price, type, description, average_rating, utilizador_id) VALUES (%s, %s, %s, %s, %s, %s, %s)'
    values = (payload['name'], payload['stock'], payload['price'], payload['type'], payload['description'], 0, user_id)

    try:
        cur.execute(statement, values)

        # commit the transaction
        conn.commit()
        response = {'status': StatusCodes['success'], 'results': f'Inserted product {payload["name"]}'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/product - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


@app.route('/dbproj/product/<product_id>', methods=['PUT'])
@token_required
def update_details(user_id,product_id):
    logger.info('PUT /dbproj/product/{product_id}')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()
    
    logger.debug(f'PUT /dbproj/product/ - payload: {payload}')

        # parameterized queries, good for security and performance
    cur.execute('SELECT id FROM product WHERE utilizador_id = %s', (user_id,))
    rows = cur.fetchall()
    user_products_id = []
    for row in rows:
        user_products_id.append(row[0])
    
    logger.info(user_products_id)
    logger.info(product_id)

    if int(product_id) not in user_products_id:
        response = {'status': StatusCodes['api_error'], 'results': f'Product not owned by user'}
        return flask.jsonify(response)
    
    logger.info(payload)
    statement = 'UPDATE product SET description = %s ,stock = %s, price = %s WHERE id = %s'
    values = (payload['description'],payload['stock'],payload['price'],product_id)

    try:
        cur.execute(statement,values)
        conn.commit()

        response = {'status': StatusCodes['success'], 'results': f'Product id:{product_id} details updated'}
        return flask.jsonify(response)
        

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'PUT /dbproj/user - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

    finally:
        if conn is not None:
            conn.close()
    
    return flask.jsonify(response)

@app.route('/dbproj/order', methods=['POST'])
@token_required
def buy_product(user_id):
    logger.info('POST /dbproj/order')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /dbproj/order - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    
    if 'cart' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'cart value not in payload'}
        return flask.jsonify(response)


    try:

        order_value = 0
        for purchase in payload["cart"]:
            logger.info(purchase)
            cur.execute("SELECT price, stock FROM product WHERE id = %s",(purchase["product_id"],))
            conn.commit()
            product_price , stock = cur.fetchone()
            if (stock < purchase['quantity']):
                response = {'status': StatusCodes['api_error'], 'results': 'insufficient stock'}
                return flask.jsonify(response)

            stock = stock - purchase['quantity']
            cur.execute('UPDATE product SET stock = %s WHERE id = %s',(stock,purchase['product_id']))
            conn.commit()

            order_value += purchase['quantity'] * product_price

            statement = 'INSERT INTO purchase(product_id, quantity, utilizador_id) VALUES (%s, %s, %s)'
            values = (purchase["product_id"],purchase['quantity'],user_id)
            cur.execute(statement, values)
            conn.commit()

        cur.execute('INSERT INTO user_order (utilizador_id,price,order_date) VALUES (%s,%s,%s) RETURNING order_id',(user_id, order_value,datetime.now(timezone.utc)))
        conn.commit()
        [new_id] = cur.fetchone() 
        response = {'status': StatusCodes['success'], 'results': f'order_id: {new_id}'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/user - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        flask.render_template('')
        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

@app.route('/dbproj/rating/<product_id>', methods=['POST'])
@token_required
def rate(user_id,product_id):
    logger.info('POST /dbproj/rating/<product_id>')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /dbproj/rating - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    
    if 'rating' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'rating value not in payload'}
        return flask.jsonify(response)
    
    # parameterized queries, good for security and performance

    cur.execute("SELECT utilizador_id, product_id FROM purchase")
    conn.commit()
    rows = cur.fetchall()
    
    found = 0
    for row in rows:
        logger.info(row)
        if int(row[0]) == int(user_id) and int(row[1]) == int(product_id):
            statement = 'INSERT INTO rating (rate_val, comment, product_id, utilizador_id) VALUES (%s, %s, %s,%s)'
            values = (payload['rating'], payload['comment'], product_id, user_id)
            found = 1

    if found == 0:
        response = {'status': StatusCodes['api_error'], 'results': 'User doesn\'t own the product'}
        return flask.jsonify(response)

    try:
        cur.execute(statement, values)

        # commit the transaction
        conn.commit()
        response = {'status': StatusCodes['success'], 'results': f'Inserted rating'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/rating  - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        flask.render_template('')
        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

@app.route('/dbproj/questions/<product_id>', methods=['POST'])
@token_required
def make_question(user_id,product_id):
    logger.info('POST /dbproj/questions/<product_id>')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /dbproj/questions/<product_id> - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    
    if 'question' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'question value not in payload'}
        return flask.jsonify(response)
    
    # parameterized queries, good for security and performance
    statement = 'INSERT INTO q_a (message,product_id) VALUES (%s, %s)'
    values = (payload['question'],product_id)

    try:
        cur.execute(statement, values)

        # commit the transaction
        conn.commit()
        response = {'status': StatusCodes['success'], 'results': f'Inserted question'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/questions/<product_id>  - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

@app.route('/dbproj/questions/<product_id>/<parent_question_id>', methods=['POST'])
@token_required
def answer_question(user_id,product_id,parent_question_id):
    logger.info('POST /dbproj/questions/<product_id>/<parent_question_id>')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /dbproj/questions/<product_id>/<parent_question_id> - payload: {payload}')

    # do not forget to validate every argument, e.g.,:
    
    if 'answer' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'answer value not in payload'}
        return flask.jsonify(response)
    
    # parameterized queries, good for security and performance
    statement = 'INSERT INTO q_a (message,product_id,parent_question_id) VALUES (%s, %s, %s)'
    values = (payload['answer'],product_id,parent_question_id)

    try:
        cur.execute(statement, values)

        # commit the transaction
        conn.commit()
        response = {'status': StatusCodes['success'], 'results': f'Inserted answer'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/questions/<product_id>  - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        # an error occurred, rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

@app.route('/dbproj/report/year', methods=['GET'])
def get_report():
    logger.info('GET /dbproj/report/year')

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT price,order_date FROM user_order WHERE EXTRACT(YEAR FROM order_date) = EXTRACT(YEAR FROM CURRENT_DATE)')
        rows = cur.fetchall()

        logger.debug('GET /dbproj/report/year - parse')

        total_orders = 0
        total_value = 0
        for row in rows:
            #t1 = datetime.strptime(row[1],)
            logger.info("TESTE")
            total_value += float(row[0])
            total_orders += 1
        content = {'total_value': total_value, 'orders': total_orders}

        response = {'status': StatusCodes['success'], 'results': content}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /dbproj/report/year - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

@app.route('/dbproj/product/<product_id>', methods=['GET'])
def product_info(product_id):
    logger.info('GET /dbproj/product/<product_id>')

    logger.debug(f'product: {id}')

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT name, id, stock, type, description, price, average_rating FROM product where id = %s', (product_id,))
        rows = cur.fetchall()

        row = rows[0]

        logger.debug('GET /dbproj/product/<product_id> - parse')
        logger.debug(row)
        content = {'name': row[0], 'product_id': row[1], 'stock': row[2], 'type': row[3] , 'description' : row[4], 'price': row[5] , 'rating': row[6] }

        response = {'status': StatusCodes['success'], 'results': content}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /dbproj/product/<product_id> - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

@app.route('/dbproj/notif', methods=['GET'])
def get_department():
    logger.info('GET /dbproj/notif')


    conn = db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('SELECT notif_id, target_user FROM notif')
        rows = cur.fetchall()
        content = []
        for row in rows:
            logger.debug('GET /dbproj/notif - parse')
            logger.debug(row)
            content.append({'notif_id': int(row[0]), 'target_user': int(row[1])}) 
            logger.info(content)

        response = {'status': StatusCodes['success'], 'results': content}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /departments/<ndep> - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)
    

##########################################################
## MAIN
##########################################################
if __name__ == "__main__":

    # Set up the logging
    logging.basicConfig(filename="logs/log_file.log")
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    time.sleep(1) #

    logger.info("\n---------------------------------------------------------------\n" + 
                  "API v1.1 online: http://localhost:8080/dbproj/\n\n")
    app.run(host="0.0.0.0", debug=True, threaded=True)
