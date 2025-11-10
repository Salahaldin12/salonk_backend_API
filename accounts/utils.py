import random
from django.core.mail import send_mail
from django.conf import settings

def generate_verification_code():
    """توليد كود تحقق عشوائي من 6 أرقام"""
    return str(random.randint(100000, 999999))

def send_verification_email(user_email, code):
    """إرسال كود التحقق عبر البريد"""
    subject = 'كود التحقق من حسابك'
    message = f'كود التحقق الخاص بك هو: {code}'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [user_email]

    send_mail(subject, message, email_from, recipient_list, fail_silently=False)



def generate_reset_code():
    return str(random.randint(100000, 999999))