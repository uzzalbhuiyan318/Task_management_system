from django.db import models
from tasks.models import CustomUser

# Create your models here.
class Message(models.Model):
    
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200, null=True)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    
    def __str__(self):
        return f"From: {self.sender.username}-To: {self.recipient.username}-{self.subject}"
    
    class Meta:
        ordering = ['-timestamp']
    