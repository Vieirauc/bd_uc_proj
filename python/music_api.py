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
    
#Funcionalidade 1
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

    elif(payload['role'] == 'consumer'):
        statement = '''
            INSERT INTO account (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id
        '''
        values = (payload['username'], payload['email'], hash_password(payload['password']))
        cur.execute(statement, values)
        account_id = cur.fetchone()[0]

        statement = '''
            INSERT INTO compilation (nome) VALUES (NULL) RETURNING id
        '''
        values = (account_id,)
        cur.execute(statement)
        top10_id = cur.fetchone()[0]

        statement = '''
            INSERT INTO consumer (account_id,premium,top10_id)
            VALUES (%s,DEFAULT,%s)
        '''
        values = (account_id,top10_id)
        cur.execute(statement, values)

        statement = '''
            INSERT INTO playlist (consumer_account_id,compilation_id) VALUES (%s,%s)
        '''
        values = (account_id,top10_id)
        cur.execute(statement,values)
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


#Funcionalidade 2
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
        consumer_user_row = cur.fetchone()

        if consumer_user_row:
            # O usuário é um usuário regular
            account_id = consumer_user_row[0]
              
            utc_dt_aware = datetime.utcnow()
            token = jwt.encode({
                'user_id': account_id,
                'role': 'consumer',
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

#Funcionalidade 3
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
    
    token = flask.request.headers['x-access-token']
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = data['user_id']
        role = data['role']
        if(role != 'artist'):
            return flask.jsonify({"alerta": "Need to be logged as artist!"}), 400
    except:
        return flask.jsonify({'alerta': 'Invalid Token!'}), 400

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

#Funcionalidade 4
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
    
    token = flask.request.headers['x-access-token']
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = data['user_id']
        role = data['role']
        if(role != 'artist'):
            return flask.jsonify({"alerta": "Need to be logged as artist!"}), 400
    except:
        return flask.jsonify({'alerta': 'Invalid Token!'}), 400

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

#Funcionalidade 5
@app.route('/dbproj/song/<keyword>', methods=['GET'])
def search_song(keyword):
    logger.info('GET /dbproj/song/<keyword>')

    conn = db_connection()
    cur = conn.cursor()

    try:
        # Execute the SQL query to retrieve songs
        statement = '''SELECT s.name, a.artistic_name, c.nome
                        FROM song s
                        JOIN artist_song asg ON s.ismn = asg.song_ismn
                        JOIN artist a ON asg.artist_account_id = a.account_id
                        JOIN position p ON s.ismn = p.song_ismn
                        JOIN compilation c ON p.compilation_id = c.id
                        JOIN album al ON c.id = al.compilation_id
                        WHERE s.name LIKE '%' || 'Bless' || '%' '''

        #TODO : Add keyword to the query
        #values = (keyword)
        #cur.execute(statement, values)
        #Nota: Por alguma razão, o código acima não funciona e dá erro no "cur.execute"

        cur.execute(statement)
        print('Executed')
        results = cur.fetchall()

        response = {'status': StatusCodes['success'], 'results': []}

        #Organize resultas by song name , artists and albums
        song_list = []
        
        i = 0
        for result in results:
            if i == 0:
                song = {'title': '', 'artists': [], 'albums': []}
                song['title'] = result[0]
            if result[0] != song['title']:
                song_list.append(song)
                song = {'title': '', 'artists': [], 'albums': []}
                song['title'] = result[0]
            if result[2] not in song['albums']:
                song['albums'].append(result[2])
            if result[1] not in song['artists']:
                song['artists'].append(result[1])
            i += 1
        song_list.append(song)

        response['results'] = song_list

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /dbproj/song/<keyword> - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

#Funcionalidade 6
@app.route('/dbproj/artist_info/<artist_id>', methods=['GET'])
def artist_info(artist_id):
    logger.info(f'GET /dbproj/artist_info/{artist_id}')

    conn = db_connection()
    cur = conn.cursor()

    try:
        # Execute the SQL query to retrieve artist information
        statement = '''SELECT a.artistic_name, array_agg(DISTINCT s.ismn) AS songs,
                            array_agg(DISTINCT al.compilation_id) AS albums,
                            array_agg(DISTINCT p.compilation_id) AS playlists
                       FROM artist a
                       LEFT JOIN artist_song asg ON a.account_id = asg.artist_account_id
                       LEFT JOIN song s ON asg.song_ismn = s.ismn
                       LEFT JOIN album al ON a.account_id = al.artist_account_id
                       LEFT JOIN position p ON al.compilation_id = p.compilation_id
                       WHERE a.account_id = %s
                       GROUP BY a.account_id
                    '''
        values = (artist_id,)
        cur.execute(statement, values)

        result = cur.fetchone()

        #TODO:
        #Não incluir albuns nas playlists

        if result:
            artist_name = result[0]
            songs = result[1] or []
            albums = result[2] or []
            playlists = result[3] or []

            response = {
                'status': StatusCodes['success'],
                'results': {
                    'name': artist_name,
                    'songs': songs,
                    'albums': albums,
                    'playlists': playlists
                }
            }
        else:
            response = {
                'status': StatusCodes['not_found'],
                'errors': f'Artist with ID {artist_id} not found'
            }

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /dbproj/artist_info/{artist_id} - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

#Funcionalidade 7
#TODO: Testar e corrigir codigo que se segue
@app.route('/dbproj/subscription', methods=['POST'])
def subscribe_to_premium():
    logger.info('POST /dbproj/subscription')

    payload = flask.request.get_json()

    # Verifying if required fields are present in the payload
    if 'period' not in payload or 'cards' not in payload:
        response = {'status': StatusCodes['bad_request'], 'errors': 'Missing required fields'}
        return flask.jsonify(response)

    period = payload['period']
    cards = payload['cards']

    conn = db_connection()
    cur = conn.cursor()

    try:
        # Execute the SQL query to insert the subscription information
        statement = '''INSERT INTO subscription (period) VALUES (%s) RETURNING id'''
        values = (period,)
        cur.execute(statement, values)

        subscription_id = cur.fetchone()[0]

        # Execute the SQL query to insert the payment information for each card
        statement = '''INSERT INTO payment (subscription_id, card_number) VALUES (%s, %s)'''
        values = [(subscription_id, card) for card in cards]
        cur.executemany(statement, values)

        conn.commit()

        response = {'status': StatusCodes['success'], 'results': subscription_id}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/subscription - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        conn.rollback()
    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

#Funcionalidade 8
#TODO: Testar e corrigir codigo que se segue
@app.route('/dbproj/playlist', methods=['POST'])
def create_playlist():
    logger.info('POST /dbproj/playlist')

    payload = flask.request.get_json()

    # Verifying if required fields are present in the payload
    if 'playlist_name' not in payload or 'visibility' not in payload or 'songs' not in payload:
        response = {'status': StatusCodes['bad_request'], 'errors': 'Missing required fields'}
        return flask.jsonify(response)

    playlist_name = payload['playlist_name']
    visibility = payload['visibility']
    songs = payload['songs']

    # Checking if user is logged in as a Premium consumer
    # Add your authentication logic here

    # If the user is not logged in or is not a Premium consumer, return an error response
    if not is_logged_in() or not is_premium_user():
        response = {'status': StatusCodes['unauthorized'], 'errors': 'Only premium consumers can create playlists'}
        return flask.jsonify(response)

    conn = db_connection()
    cur = conn.cursor()

    try:
        # Execute the SQL query to insert the playlist information
        statement = '''INSERT INTO playlist (name, visibility) VALUES (%s, %s) RETURNING id'''
        values = (playlist_name, visibility)
        cur.execute(statement, values)

        playlist_id = cur.fetchone()[0]

        # Execute the SQL query to insert the song entries in the playlist
        statement = '''INSERT INTO playlist_song (playlist_id, song_id) VALUES (%s, %s)'''
        values = [(playlist_id, song) for song in songs]
        cur.executemany(statement, values)

        conn.commit()

        response = {'status': StatusCodes['success'], 'results': {'playlist_id': playlist_id}}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/playlist - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        conn.rollback()
    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

#Funcionalidade 9
@app.route('/dbproj/<int:song_ismn>', methods=['PUT'])
@token_required
def play_song(user_id, song_ismn):
    logger.info(f'PUT /dbproj/{song_ismn}')

    # Get the current user's top 10 played songs
    user_top_songs = get_user_top_songs(user_id)

    # Increment the play count for the played song
    update_play_count(song_ismn)

    # Update the user's top 10 played songs if necessary
    if song_ismn in user_top_songs:
        user_top_songs.remove(song_ismn)
    user_top_songs.append(song_ismn)
    user_top_songs = sorted(user_top_songs, key=lambda x: get_play_count(x), reverse=True)[:10]
    update_user_top_songs(user_id, user_top_songs)

    response = {'status': StatusCodes['success']}
    return flask.jsonify(response)

#Funcionalidade 10
@app.route('/dbproj/card', methods=['POST'])
@token_required
def generate_cards(user_id):
    logger.info('POST /dbproj/card')
    payload = flask.request.get_json()

    num_cards = payload.get('number_cards')
    card_price = payload.get('card_price')

    if not num_cards or not card_price:
        response = {'status': StatusCodes['bad_request'], 'errors': 'Both number_cards and card_price are required'}
        return flask.jsonify(response)

    try:
        conn = db_connection()
        cur = conn.cursor()

        card_ids = []
        for i in range(num_cards):
            cur.execute('INSERT INTO prepaid_card (price, created_by) VALUES (%s, %s) RETURNING id', (card_price, user_id))
            card_id = cur.fetchone()[0]
            card_ids.append(card_id)

        conn.commit()

        response = {'status': StatusCodes['success'], 'results': card_ids}
        return flask.jsonify(response)

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/card - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)


#Funcionalidade 11
@app.route('/dbproj/comments/<song_id>', methods=['POST'])
@token_required
def leave_comment(user_id, song_id):
    logger.info(f'POST /dbproj/comments/{song_id}')

    payload = flask.request.get_json()

    # Verifying if required field is present in the payload
    if 'comment' not in payload:
        response = {'status': StatusCodes['bad_request'], 'errors': 'Missing required field'}
        return flask.jsonify(response)

    comment = payload['comment']

    conn = db_connection()
    cur = conn.cursor()

    try:
        # Insert the top-level comment
        statement = '''INSERT INTO comment (song_ismn, body, consumer_account_id,datetime) VALUES (%s, %s, %s, %s) RETURNING id'''
        values = (song_id,comment,user_id, datetime.now())
        cur.execute(statement, values)

        comment_id = cur.fetchone()[0]
        conn.commit()

        response = {'status': StatusCodes['success'], 'results': {'comment_id': comment_id}}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/comments/{song_id} - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        conn.rollback()
    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

#Funcionalidade 11.1
@app.route('/dbproj/comments/<song_id>/<parent_comment_id>', methods=['POST'])
@token_required
def reply_comment(user_id,song_id, parent_comment_id):
    logger.info(f'POST /dbproj/comments/{song_id}')

    payload = flask.request.get_json()

    # Verifying if required field is present in the payload
    if 'comment' not in payload:
        response = {'status': StatusCodes['bad_request'], 'errors': 'Missing required field'}
        return flask.jsonify(response)

    comment = payload['comment']

    conn = db_connection()
    cur = conn.cursor()

    try:

        # Check if the parent comment exists
        statement = '''SELECT id FROM comment WHERE id = %s'''
        values = (parent_comment_id,)
        cur.execute(statement, values)

        parent_comment = cur.fetchone()

        # Insert the reply comment
        statement = '''INSERT INTO comment (song_ismn, body, datetime, consumer_account_id, comment_id) VALUES (%s, %s, %s, %s,%s) RETURNING id'''
        values = (song_id, comment, datetime.now(), user_id ,parent_comment_id)
        cur.execute(statement, values)

        comment_id = cur.fetchone()[0]
        conn.commit()

        response = {'status': StatusCodes['success'], 'results': {'comment_id': comment_id}}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/comments/{song_id} - error: {error}')
        response = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        conn.rollback()
    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(response)

#Funcionalidade 12
#TODO: Testar e corrigir codigo que se segue
@app.route('/dbproj/report/<year_month>', methods=['GET'])
def generate_monthly_report(year_month):
    logger.info(f'GET /dbproj/report/{year_month}')

    year, month = year_month.split('-')

    conn = db_connection()
    cur = conn.cursor()

    try:
        # Execute the SQL query to retrieve the monthly report
        statement = '''
            SELECT EXTRACT(MONTH FROM playback_time) AS month, genre, COUNT(*) AS playbacks
            FROM playback
            JOIN song ON playback.song_id = song.id
            WHERE EXTRACT(YEAR FROM playback_time) = %s
                AND EXTRACT(MONTH FROM playback_time) >= %s
            GROUP BY EXTRACT(MONTH FROM playback_time), genre
            ORDER BY month, genre
        '''
        values = (year, month)
        cur.execute(statement, values)

        results = cur.fetchall()

        response = {'status': StatusCodes['success'], 'results': []}
        for result in results:
            month_name = calendar.month_name[int(result[0])]
            genre = result[1]
            playbacks = result[2]
            response['results'].append({'month': month_name, 'genre': genre, 'playbacks': playbacks})

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /dbproj/report/{year_month} - error: {error}')
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
