import os
import secrets
import logging
from flask import Flask, render_template, request, redirect, url_for, session, abort
from flask_mail import Mail, Message
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from markupsafe import escape
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ──────────────────────────────────────────────
# CONFIGURACIÓN DE SEGURIDAD
# ──────────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ──────────────────────────────────────────────
# MAIL — Microsoft 365
# ──────────────────────────────────────────────
app.config['MAIL_SERVER']         = 'smtp.office365.com'
app.config['MAIL_PORT']           = 587
app.config['MAIL_USE_TLS']        = True
app.config['MAIL_USERNAME']       = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD']       = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)

# ──────────────────────────────────────────────
# RATE LIMITING
# ──────────────────────────────────────────────
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri='memory://',
)

# Soporta múltiples destinatarios separados por coma
# Ejemplo: leads@setec-cr.com,ventas@setec-cr.com,gerencia@setec-cr.com
_dest_raw   = os.environ.get('DEST_EMAIL', 'leads@setec-cr.com')
DEST_EMAILS = [e.strip() for e in _dest_raw.split(',') if e.strip()]

# ──────────────────────────────────────────────
# CABECERAS DE SEGURIDAD HTTP
# ──────────────────────────────────────────────
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options']  = 'nosniff'
    response.headers['X-Frame-Options']          = 'SAMEORIGIN'
    response.headers['X-XSS-Protection']         = '1; mode=block'
    response.headers['Referrer-Policy']           = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy']        = 'geolocation=(), microphone=(), camera=()'
    response.headers['Content-Security-Policy']   = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data:; "
        "frame-src https://maps.google.com https://www.google.com; "
        "connect-src 'self';"
    )
    return response

# ──────────────────────────────────────────────
# CSRF — helpers
# ──────────────────────────────────────────────
def generate_csrf():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)
    return session['csrf_token']

def validate_csrf(token):
    return token and token == session.get('csrf_token')

app.jinja_env.globals['csrf_token'] = generate_csrf

# ──────────────────────────────────────────────
# HOME
# ──────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

# ──────────────────────────────────────────────
# SOBRE NOSOTROS
# ──────────────────────────────────────────────
@app.route('/sobre-nosotros/')
def sobre_nosotros():
    return render_template('sobre_nosotros.html')

# ──────────────────────────────────────────────
# PRODUCTOS Y SERVICIOS
# ──────────────────────────────────────────────
@app.route('/lavanderia-industrial/')
def lavanderia_industrial():
    return render_template('lavanderia_industrial.html')

@app.route('/trasiego-de-fluidos/')
def trasiego_de_fluidos():
    return render_template('trasiego_de_fluidos.html')

@app.route('/sistemas-de-vapor-y-agua-caliente/')
def sistemas_vapor():
    return render_template('sistemas_vapor.html')

@app.route('/recubrimientos/')
def recubrimientos():
    return render_template('recubrimientos.html')

# ──────────────────────────────────────────────
# INSTRUMENTACIÓN ANALÍTICA
# ──────────────────────────────────────────────
@app.route('/instrumentacion-analitica/')
def instrumentacion_analitica():
    return render_template('instrumentacion_analitica/index.html')

@app.route('/instrumentacion-analitica/mettler-toledo/')
def mettler_toledo():
    return render_template('instrumentacion_analitica/mettler_toledo.html')

@app.route('/instrumentacion-analitica/memmert/')
def memmert():
    return render_template('instrumentacion_analitica/memmert.html')

@app.route('/instrumentacion-analitica/scilogex-2/')
def scilogex():
    return render_template('instrumentacion_analitica/scilogex.html')

@app.route('/otras-marcas/')
def otras_marcas():
    return render_template('instrumentacion_analitica/otras_marcas.html')

# ──────────────────────────────────────────────
# BLOG
# ──────────────────────────────────────────────
@app.route('/blog/')
def blog():
    return render_template('blog.html')

# ──────────────────────────────────────────────
# CONTACTO
# ──────────────────────────────────────────────
@app.route('/contacto/', methods=['GET', 'POST'])
@limiter.limit('5 per minute; 20 per hour', methods=['POST'])
def contacto():
    sent  = False
    error = False

    if request.method == 'POST':
        # CSRF validation
        if not validate_csrf(request.form.get('csrf_token')):
            logger.warning('CSRF token inválido desde %s', request.remote_addr)
            abort(403)

        # Honeypot — bots llenan este campo, humanos no
        if request.form.get('website', ''):
            logger.warning('Honeypot activado desde %s', request.remote_addr)
            sent = True  # respuesta silenciosa al bot
            return render_template('contacto.html', sent=sent, error=error)

        nombre   = escape(request.form.get('nombre',   ''))
        email_u  = escape(request.form.get('email',    ''))
        telefono = escape(request.form.get('telefono', ''))
        empresa  = escape(request.form.get('empresa',  ''))
        asunto   = escape(request.form.get('asunto',   ''))
        mensaje  = escape(request.form.get('mensaje',  ''))

        html_body = f"""
        <html><body style="font-family:Arial,sans-serif;color:#333;">
          <h2 style="color:#0d1b5e;"> Nueva solicitud de contacto </h2>
          <table cellpadding="8" style="border-collapse:collapse;width:100%;max-width:600px;">
            <tr style="background:#f5f5f5;">
              <td style="font-weight:bold;width:130px;">Nombre</td><td>{nombre}</td>
            </tr>
            <tr>
              <td style="font-weight:bold;">Email</td>
              <td><a href="mailto:{email_u}">{email_u}</a></td>
            </tr>
            <tr style="background:#f5f5f5;">
              <td style="font-weight:bold;">Teléfono</td><td>{telefono}</td>
            </tr>
            <tr>
              <td style="font-weight:bold;">Empresa</td><td>{empresa}</td>
            </tr>
            <tr style="background:#f5f5f5;">
              <td style="font-weight:bold;">Asunto</td><td>{asunto}</td>
            </tr>
            <tr>
              <td style="font-weight:bold;vertical-align:top;">Mensaje</td>
              <td style="white-space:pre-wrap;">{mensaje}</td>
            </tr>
          </table>
          <p style="margin-top:1.5rem;font-size:.85rem;color:#888;">
            Enviado desde el formulario de contacto de setec-cr.com
          </p>
        </body></html>
        """

        try:
            msg = Message(
                subject=f"SETEC Web Lead | {empresa} – {nombre}",
                recipients=DEST_EMAILS,   # todos reciben el mismo lead
                html=html_body,
                reply_to=str(email_u),    # responder va directo al cliente
            )
            mail.send(msg)
            sent = True
            logger.info('Lead enviado a %s desde %s', DEST_EMAILS, request.remote_addr)
        except Exception as e:
            logger.error('Error al enviar correo: %s', e)
            error = True

    return render_template('contacto.html', sent=sent, error=error)

# ──────────────────────────────────────────────
# PÁGINAS LEGALES
# ──────────────────────────────────────────────
@app.route('/terminos-y-condiciones/')
def terminos():
    return render_template('terminos.html')

@app.route('/politicas-de-privacidad/')
def privacidad():
    return render_template('privacidad.html')

@app.route('/cookies/')
def cookies():
    return render_template('cookies.html')

@app.route('/politicas-de-reembolso/')
def reembolso():
    return render_template('reembolso.html')

# ──────────────────────────────────────────────
# REDIRECTS de URLs sin trailing slash
# ──────────────────────────────────────────────
@app.route('/sobre-nosotros')
@app.route('/lavanderia-industrial')
@app.route('/trasiego-de-fluidos')
@app.route('/sistemas-de-vapor-y-agua-caliente')
@app.route('/recubrimientos')
@app.route('/instrumentacion-analitica')
@app.route('/instrumentacion-analitica/mettler-toledo')
@app.route('/instrumentacion-analitica/memmert')
@app.route('/instrumentacion-analitica/scilogex-2')
@app.route('/otras-marcas')
@app.route('/blog')
@app.route('/contacto')
@app.route('/terminos-y-condiciones')
@app.route('/politicas-de-privacidad')
@app.route('/cookies')
@app.route('/politicas-de-reembolso')
def redirect_no_slash():
    return redirect(request.path + '/', 301)

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug)
