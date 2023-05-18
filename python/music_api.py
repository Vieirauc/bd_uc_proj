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
 
import hashlib
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
## UTILITY FUNCTIONS
#########################################################
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def check_password(password, hash):
    hashed = hash_password(password)
    if hashed.strip() == hash.strip():
        return True
    else:
        return False

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
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
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
        host = '127.0.0.1',
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
    
    if 'username' not in payload or 'email' not in payload or 'password' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'username, email or password value not in payload'}
        return flask.jsonify(response)
    
    if 'role' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'role value not in payload'}
        return flask.jsonify(response)
    
    # parameterized queries, good for security and performance
    if(payload['role'] == 'admin'):
        statement = '''
            INSERT INTO account (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id
        '''
        values = (payload['username'], payload['email'], hash_password(payload['password']))
        cur.execute(statement, values)
        account_id = cur.fetchone()[0]

        statement = '''
            INSERT INTO administrator (account_id)
            VALUES (%s)
        '''
        values = (account_id,)
        cur.execute(statement, values)
        conn.commit()

        response = {'status': StatusCodes['success'], 'results': f'User {payload["username"]} created'}
        return flask.jsonify(response)

    elif(payload['role'] == 'regular'):
        statement = '''
            INSERT INTO account (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id
        '''
        values = (payload['username'], payload['email'], hash_password(payload['password']))
        cur.execute(statement, values)
        account_id = cur.fetchone()[0]

        statement = '''
            INSERT INTO regular (account_id)
            VALUES (%s)
        '''
        values = (account_id,)
        cur.execute(statement, values)
        conn.commit()

        response = {'status': StatusCodes['success'], 'results': f'User {payload["username"]} created'}
        return flask.jsonify(response)
        
    #Add artist and resquest admin token in header
    elif(payload['role'] == 'artist'):
        if 'admin-token' in flask.request.headers:
            token = flask.request.headers['admin-token']

        if not token:
            return flask.jsonify({"alerta": "Missing Admin Token!"}), 400
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            user_id = data['user_id']
            role = data['role']
            if(role != 'admin'):
                return flask.jsonify({"alerta": "Need admin permission!"}), 400
        except:
            return flask.jsonify({'alerta': 'Invalid Token!'}), 400
        
        statement = '''
            INSERT INTO account (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id
        '''
        values = (payload['username'], payload['email'], hash_password(payload['password']))
        cur.execute(statement, values)
        account_id = cur.fetchone()[0]

        statement = '''
            WITH publisher_id_cte AS (
            SELECT id
            FROM publisher
            WHERE name = %s
            )
            INSERT INTO artist (account_id, artistic_name, publisher_id)
            VALUES (%s, %s, (SELECT id FROM publisher_id_cte));
        '''
        values = (payload['publisher'],account_id,payload['artistic_name'])
        cur.execute(statement, values)
        conn.commit()

        response = {'status': StatusCodes['success'], 'results': f'User {payload["username"]} created'}

    return flask.jsonify(response)


@app.route('/dbproj/user', methods=['PUT'])
def login_user():
    logger.info('PUT /dbproj/user')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()
    
    logger.debug(f'PUT /dbproj/user - payload: {payload}')

    # Verificar se todos os campos obrigatórios estão presentes no payload
    required_fields = ['username', 'password']
    missing_fields = [field for field in required_fields if field not in payload]

    if missing_fields:
        response = {'status': StatusCodes['api_error'], 'results': f'Missing fields: {", ".join(missing_fields)}'}
        return flask.jsonify(response)

    username = payload['username']
    password = payload['password']

    try:
        # Consultar a tabela "administrator" para verificar se o usuário é um admin
        statement = '''
            SELECT account.id FROM administrator
            INNER JOIN account ON administrator.account_id = account.id
            WHERE account.username = %s AND account.password_hash = %s
        '''
        values = (username, hash_password(password))
        cur.execute(statement, values)
        admin_row = cur.fetchone()

        if admin_row:
            # O usuário é um admin
            account_id = admin_row[0]

            utc_dt_aware = datetime.utcnow()
            token = jwt.encode({
                'user_id': account_id,
                'role': 'admin',
                'exp': utc_dt_aware + timedelta(minutes = 120)
            },
                app.config['SECRET_KEY'], algorithm='HS256')
            
            response = {'status': StatusCodes['success'], 'results': f'Logged in as {payload["username"]}'}
            return flask.jsonify({'token': token})
            

        # Consultar a tabela "artist" para verificar se o usuário é um artista
        statement = '''
            SELECT account.id FROM artist
            INNER JOIN account ON artist.account_id = account.id
            WHERE account.username = %s AND account.password_hash = %s
        '''
        values = (username, hash_password(password))
        cur.execute(statement, values)
        artist_row = cur.fetchone()

        if artist_row:
            # O usuário é um artista
            account_id = admin_row[0]

            utc_dt_aware = datetime.utcnow()
            token = jwt.encode({
                'user_id': account_id,
                'role': 'artist',
                'exp': utc_dt_aware + timedelta(minutes = 120)
            },
                app.config['SECRET_KEY'], algorithm='HS256')
            
            response = {'status': StatusCodes['success'], 'results': f'Logged in as {payload["username"]}'}
            return flask.jsonify({'token': token})
        
        # Se o usuário não foi encontrado nas tabelas "administrator" e "artist",
        # ele é considerado um usuário regular
        statement = 'SELECT id FROM account WHERE username = %s AND password_hash = %s'
        values = (username, hash_password(password))
        cur.execute(statement, values)
        regular_user_row = cur.fetchone()

        if regular_user_row:
            # O usuário é um usuário regular
            account_id = regular_user_row[0]
              
            utc_dt_aware = datetime.utcnow()
            token = jwt.encode({
                'user_id': account_id,
                'role': 'artist',
                'exp': utc_dt_aware + timedelta(minutes = 120)
            },
                app.config['SECRET_KEY'], algorithm='HS256')
            
            response = {'status': StatusCodes['success'], 'results': f'Logged in as {payload["username"]}'}
            return flask.jsonify({'token': token})

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/login - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

@app.route('/dbproj/song', methods=['POST'])
@token_required
def add_song(user_id):
    logger.info('POST /dbproj/song')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /dbproj/song - payload: {payload}')

    # Verificar se todos os campos obrigatórios estão presentes no payload
    required_fields = ['song_name', 'release_date', 'publisher', 'other_artists', 'duration', 'ismn', 'genre']
    missing_fields = [field for field in required_fields if field not in payload]

    if missing_fields:
        response = {'status': StatusCodes['api_error'], 'results': f'Missing fields: {", ".join(missing_fields)}'}
        return flask.jsonify(response)

    song_name = payload['song_name']
    release_date = payload['release_date']
    publisher_id = payload['publisher']
    other_artists = payload['other_artists']
    duration = payload['duration']
    ismn = payload['ismn']
    genre = payload['genre']
    
    # Get id of current user from token

    try:
        # Inserir a música na tabela "song"
        statement = '''
            INSERT INTO song (ismn, name, release_date, genre, duration, artist_account_id, publisher_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING ismn
        '''
        values = (ismn, song_name, release_date, genre, duration, user_id, publisher_id)
        cur.execute(statement, values)
        song_id = cur.fetchone()[0]

        # Inserir a relação entre o artista atual e a música na tabela "artist_song"
        statement = '''
            INSERT INTO artist_song (artist_account_id, song_ismn)
            VALUES (%s, %s)
        '''
        values = (user_id, ismn)
        cur.execute(statement, values)

        # Inserir as relações entre os outros artistas e a música na tabela "artist_song"
        for artist_id in other_artists:
            statement = '''
                INSERT INTO artist_song (artist_account_id, song_ismn)
                VALUES (%s, %s)
            '''
            values = (artist_id, ismn)
            cur.execute(statement, values)

        # Commit a transação
        conn.commit()
        response = {'status': StatusCodes['success'], 'results': f'Inserted song with ID: {song_id}'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/song - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        # Ocorreu um erro, faz rollback
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

@app.route('/dbproj/album', methods=['POST'])
@token_required
def add_album():
    logger.info('POST /dbproj/album')
    payload = flask.request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.debug(f'POST /dbproj/album - payload: {payload}')

    if 'name' not in payload or 'release_date' not in payload or 'publisher' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'name, release_date, or publisher value not in payload'}
        return flask.jsonify(response)

    if 'songs' not in payload:
        response = {'status': StatusCodes['api_error'], 'results': 'songs value not in payload'}
        return flask.jsonify(response)

    try:
        # Insert the album into the album table
        statement = 'INSERT INTO album (compilation_id, artist_account_id) VALUES (DEFAULT, %s) RETURNING compilation_id'
        values = (payload['publisher'],)
        cur.execute(statement, values)
        compilation_id = cur.fetchone()[0]

        # Insert the songs into the song table and their relationships with the album
        for song_data in payload['songs']:
            if isinstance(song_data, int):
                # Existing song, associate it with the album
                statement = 'INSERT INTO position (position, song_ismn, compilation_id) VALUES (DEFAULT, %s, %s)'
                values = (song_data, compilation_id)
                cur.execute(statement, values)
            elif isinstance(song_data, dict):
                # New song, follow the same process as adding a single song
                statement = 'INSERT INTO song (name, release_date, publisher_id) VALUES (%s, %s, %s) RETURNING ismn'
                values = (song_data['song_name'], song_data['release_date'], song_data['publisher'])
                cur.execute(statement, values)
                song_ismn = cur.fetchone()[0]

                for artist_id in song_data.get('other_artists', []):
                    statement = 'INSERT INTO artist_song (artist_account_id, song_ismn) VALUES (%s, %s)'
                    values = (artist_id, song_ismn)
                    cur.execute(statement, values)

                statement = 'INSERT INTO position (position, song_ismn, compilation_id) VALUES (DEFAULT, %s, %s)'
                values = (song_ismn, compilation_id)
                cur.execute(statement, values)

        # Commit the transaction
        conn.commit()
        response = {'status': StatusCodes['success'], 'results': f'Successfully added album with ID: {compilation_id}'}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/album - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        # An error occurred, rollback
        conn.rollback()

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

    host = '127.0.0.1'
    port = 8080
    logger.info("\n---------------------------------------------------------------\n" + 
                  "API v1.1 online: http://localhost:8080/\n\n")
    app.run(host=host, debug=True, threaded=True, port=port)