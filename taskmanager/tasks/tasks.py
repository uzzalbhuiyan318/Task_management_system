from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

@shared_task
def send_email_task(subject, to_email, task_context):
    """
    A Celery task to send an email asynchronously.
    """
    # We pass 'task_context' as a dictionary because Celery can't serialize Django model objects directly.
    html_message = render_to_string('email_notification.html', {'task': task_context})
    plain_message = strip_tags(html_message)
    from_email = 'donotreply@taskmanager.com'

    send_mail(
        subject,
        plain_message,
        from_email,
        [to_email],
        html_message=html_message
    )
    return f"Email sent to {to_email}"
