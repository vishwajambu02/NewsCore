import requests
from flask import current_app


def send_otp_email(to_email, code, purpose='login'):
    api_key = current_app.config.get('BREVO_API_KEY')
    if not api_key:
        current_app.logger.error('BREVO_API_KEY not set — cannot send OTP')
        return False

    subject = 'Your NewsCore verification code' if purpose == 'signup' else 'Your NewsCore login code'

    payload = {
        'sender': {'name': 'NewsCore', 'email': current_app.config.get('MAIL_FROM', 'vishwajambu66@gmail.com')},
        'to': [{'email': to_email}],
        'subject': subject,
        'htmlContent': f'''
            <div style="font-family:Inter,sans-serif;background:#0a0a0f;color:#fff;padding:32px;">
                <h2 style="color:#ff6b35;">NewsCore</h2>
                <p>Your verification code is:</p>
                <p style="font-size:32px;font-weight:700;letter-spacing:4px;">{code}</p>
                <p style="color:#888;font-size:13px;">Expires in 10 minutes. If you did not request this, ignore this email.</p>
            </div>
        '''
    }

    try:
        resp = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={'api-key': api_key, 'Content-Type': 'application/json', 'accept': 'application/json'},
            json=payload,
            timeout=10
        )
        if resp.status_code not in (200, 201):
            current_app.logger.error(f'Brevo API error {resp.status_code}: {resp.text}')
            print(f'[EmailService] Brevo API error {resp.status_code}: {resp.text}')
            return False
        return True
    except requests.RequestException as e:
        current_app.logger.error(f'Brevo send failed: {e}')
        print(f'[EmailService] Brevo send failed: {e}')
        return False


def send_contact_message(name, from_email, message):
    """Sends a contact-form submission to the site owner's inbox via Brevo."""
    api_key = current_app.config.get('BREVO_API_KEY')
    if not api_key:
        current_app.logger.error('BREVO_API_KEY not set — cannot send contact message')
        return False

    owner_email = current_app.config.get('MAIL_FROM', 'vishwajambu66@gmail.com')

    payload = {
        'sender': {'name': 'NewsCore Contact Form', 'email': owner_email},
        'to': [{'email': owner_email}],
        'replyTo': {'email': from_email, 'name': name},
        'subject': f'New contact message from {name}',
        'htmlContent': f'''
            <div style="font-family:Inter,sans-serif;background:#0a0a0f;color:#fff;padding:32px;">
                <h2 style="color:#ff6b35;">New Contact Message</h2>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {from_email}</p>
                <p><strong>Message:</strong></p>
                <p style="white-space:pre-wrap;">{message}</p>
            </div>
        '''
    }

    try:
        resp = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={'api-key': api_key, 'Content-Type': 'application/json', 'accept': 'application/json'},
            json=payload,
            timeout=10
        )
        if resp.status_code not in (200, 201):
            current_app.logger.error(f'Brevo contact-send error {resp.status_code}: {resp.text}')
            print(f'[EmailService] Brevo contact-send error {resp.status_code}: {resp.text}')
            return False
        return True
    except requests.RequestException as e:
        current_app.logger.error(f'Brevo contact-send failed: {e}')
        print(f'[EmailService] Brevo contact-send failed: {e}')
        return False