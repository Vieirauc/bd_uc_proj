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
            account_id = artist_row[0]

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
def add_album(user_id):
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

        # Inserir uma nova entrada na tabela "compilation"
        cur.execute("INSERT INTO compilation (nome) VALUES (%s) RETURNING id", (payload['name'],))
        compilation_id = cur.fetchone()[0]

        # Insert the album into the album table
        statement = 'INSERT INTO album (compilation_id, artist_account_id) VALUES (%s, %s) RETURNING compilation_id'
        values = (compilation_id,payload['publisher'])
        cur.execute(statement, values)

        #Starting position
        position = 1
        # Insert the songs into the song table and their relationships with the album
        for song_data in payload['songs']:
            if isinstance(song_data, int):
                # Existing song, associate it with the album
                statement = 'INSERT INTO position (position, song_ismn, compilation_id) VALUES (%s, %s, %s)'
                values = (position,song_data, compilation_id)
                cur.execute(statement, values)
            elif isinstance(song_data, dict):
                # New song, follow the same process as adding a single song
                statement = 'INSERT INTO song (name, release_date, publisher_id, ismn, genre, duration , artist_account_id) VALUES (%s, %s, %s, %s, %s, %s, %s)'
                values = (song_data['song_name'], song_data['release_date'], song_data['publisher'], song_data['ismn'], song_data['genre'], song_data['duration'], user_id)
                cur.execute(statement, values)

                for artist_id in song_data.get('other_artists', []):
                    statement = 'INSERT INTO artist_song (artist_account_id, song_ismn) VALUES (%s, %s)'
                    values = (artist_id, song_data['ismn'])
                    cur.execute(statement, values)

                statement = 'INSERT INTO position (position, song_ismn, compilation_id) VALUES (%s, %s, %s)'
                values = (position,song_data['ismn'], compilation_id)
                cur.execute(statement, values)
            position += 1

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
