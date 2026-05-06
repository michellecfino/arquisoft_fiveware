from django.db import models

class AuditLog(models.Model):
    user_id = models.CharField(max_length=100)
    role = models.CharField(max_length=50)
    service = models.CharField(max_length=100)
    action = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        #Evita UPDATE
        if self.pk is not None:
            raise Exception("Audit logs are immutable (UPDATE not allowed)")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Evita DELETE
        raise Exception("Audit logs are immutable (DELETE not allowed)")

    class Meta:
        db_table = "audit_logs"
