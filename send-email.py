import smtplib, sqlalchemy
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy.exc import SQLAlchemyError

db_connect = sqlalchemy.create_engine(
    sqlalchemy.engine.url.URL(
        drivername="mysql+pymysql",
        username="root",
        password="admin123",
        database="zurich",
        query={"unix_socket": "/cloudsql/myprojectmostqi:southamerica-east1:myinstance"},
    ),
)

HOST_NAME = 'smtp.gmail.com'
HOST_PORT = 465
EMAIL_FROM = 'luisfelipenovais98@gmail.com'
EMAIL_PASSWORD = 'qjablgrefyyethjv'

def sendEmail(request):
    conn = db_connect.connect()
    metadata = sqlalchemy.MetaData()

    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        # Allows POST requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Origin, Content-Type, X-Auth-Token, application, token',
            'Access-Control-Max-Age': '3600',
            'Access-Control-Allow-Credentials': 'true'
        }

        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    # VALIDA SE CÓDIGO DE TEMPLATE ENVIADO É VÁLIDO
    if request.json['idMessage'] != '':
        message = sqlalchemy.Table(
            'message',
            metadata,
            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column('body', sqlalchemy.Text),
            sqlalchemy.Column('subject', sqlalchemy.String),
            sqlalchemy.Column('recipient', sqlalchemy.String),
            sqlalchemy.Column('copy', sqlalchemy.String),
        )

        templates = sqlalchemy.select([message]).where(message.c.id == str(request.json['idMessage']))

        result = conn.execute(templates)
        # Se for válido continua com o processo
        if result.rowcount > 0:
            template = result.fetchone()

            msg = MIMEMultipart() # create a message

            data = formatData(request.json)
            html_content = createContent(data, template['body'])

            # setup the parameters of the message
            msg['From']='no-reply@gmail.com'
            msg['To']=template['recipient']
            msg['Cc']=template['copy']
            msg['Subject']=template['subject']
            toaddrs = [msg['To']] + [msg['Cc']]
            
            # add in the message body
            msg.attach(MIMEText(html_content, 'html'))

            # set up the SMTP server
            s = smtplib.SMTP_SSL(host=HOST_NAME)
            s.login(EMAIL_FROM, EMAIL_PASSWORD)
            s.sendmail(EMAIL_FROM, toaddrs, msg.as_string())
            s.quit()

        else:
            return ({"data": {"message": "Nenhum template de mensagem encontrada com o ID fornecido.", "status": "Erro."}}, 403)   

    else:
        return ({"data": {"message": "ID do template invalido.", "status": "Erro."}}, 403)   

def formatData(json):
    if json['tipoSeguro'] == "":
        json['tipoSeguro'] = "Não foi possível abrir, o tipo de seguro não foi indicado"
    if json['dataOcorrencia'] == "":
        json['dataOcorrencia'] = "Não foi possível abrir, a data de ocorrência não foi capturada"
    if json['cpfContato'] == "":
        json['cpfContato'] = "Não foi possível abrir, o cpf do contato não foi indicado"
    if json['emailContato'] == "":
        json['emailContato'] = "Não foi possível abrir, o email de contato não foi indicado"
    if json['telefoneContato'] == "":
        json['telefoneContato'] = "Não foi possível abrir, o telefone de contato não foi indicado"

    return json

def createContent(data, content):
    keywords = getKeywords(content)

    for row in range(0, len(keywords)):
        key = keywords[row]
        text = "{" + key + "}"
        if (data[key]):
            content = content.replace(text, data[key])
        else:
            content = content.replace(text, '')

    return content

def getKeywords(text):
    middleWords = text.split("{")
    result = []
    for row in range(1, len(middleWords)):
        if ('}' in middleWords[row]):
            word = middleWords[row].split('}')
            result.append(word[0])

    return result