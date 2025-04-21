import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import sqlite3

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'None'  
SMTP_PASSWORD = 'None'               
FROM_EMAIL = 'notification@gmail.com'    

def get_db():
    conn = sqlite3.connect('petfinder.db')
    conn.row_factory = sqlite3.Row
    return conn

def send_email(to_email, subject, html_content):
    """
    Send an email with HTML content
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email

        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def notify_match_by_email(user_id, match_data):
    """
    Send an email notification about a potential match
    """
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT email, notification_preferences FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return False
            
        email = user['email']
        prefs = user['notification_preferences']
        
        if not prefs:
            prefs = '{}'
            
        prefs = eval(prefs) if isinstance(prefs, str) else prefs
        
        if not prefs.get('email_enabled', False):
            return False
            
        subject = "Найдено возможное совпадение для вашего питомца!"
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
                .button {{ background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Найдено возможное совпадение!</h1>
                </div>
                <div class="content">
                    <p>Здравствуйте!</p>
                    <p>Мы нашли возможное совпадение для вашего питомца:</p>
                    <ul>
                        <li><strong>Порода:</strong> {match_data.get('breed', 'Не указана')}</li>
                        <li><strong>Категория:</strong> {match_data.get('category', 'Не указана')}</li>
                        <li><strong>Место:</strong> {match_data.get('location', 'Не указано')}</li>
                        <li><strong>Сходство:</strong> {int(match_data.get('similarity_score', 0) * 100)}%</li>
                    </ul>
                    <p>Для просмотра деталей перейдите на сайт.</p>
                    <p><a href="http://localhost:5000" class="button">Перейти на сайт</a></p>
                </div>
                <div class="footer">
                    <p>Это автоматическое уведомление. Пожалуйста, не отвечайте на это письмо.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return send_email(email, subject, html_content)
        
    except Exception as e:
        print(f"Error in notify_match_by_email: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def send_no_match_confirmation_email(user_id, pet_data):
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT email FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return False
            
        email = user['email']
        
        subject = "Подтверждение подписки на уведомления о совпадениях"
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
                .button {{ background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Подписка на уведомления</h1>
                </div>
                <div class="content">
                    <p>Здравствуйте!</p>
                    <p>К сожалению, мы не нашли совпадений для вашего питомца:</p>
                    <ul>
                        <li><strong>Тип:</strong> {pet_data.get('type', 'Не указан')}</li>
                        <li><strong>Порода:</strong> {pet_data.get('breed', 'Не указана')}</li>
                        <li><strong>Категория:</strong> {pet_data.get('category', 'Не указана')}</li>
                    </ul>
                    <p>Мы будем продолжать поиск и уведомим вас, если найдем совпадение.</p>
                    <p>Вы можете изменить настройки уведомлений в любое время на нашем сайте.</p>
                    <p><a href="http://localhost:5000" class="button">Перейти на сайт</a></p>
                </div>
                <div class="footer">
                    <p>Это автоматическое уведомление. Пожалуйста, не отвечайте на это письмо.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return send_email(email, subject, html_content)
        
    except Exception as e:
        print(f"Error in send_no_match_confirmation_email: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()
