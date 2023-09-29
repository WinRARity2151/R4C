from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Robot
from orders.models import Order

@receiver(post_save, sender=Robot)
def notify_customers(sender, instance, **kwargs):
    orders = Order.objects.filter(robot_serial=instance.serial)
    if orders.exists():
        subject = 'Робот в наличии'
        message = f'Добрый день!\nНедавно вы интересовались роботом модели {instance.model}, версии {instance.version} с серийным номером {instance.serial}.\nЭтот робот теперь в наличии. Если вам подходит этот вариант - пожалуйста, свяжитесь с нами.'
        from_email = 'danil.dya4enko@mail.ru'

        for order in orders:
            recipient_email = order.customer.email
            send_mail(subject, message, from_email, [recipient_email], fail_silently=False)
