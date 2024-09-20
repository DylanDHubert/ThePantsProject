from django.db import models

class FileCoordinate(models.Model):
    filename = models.CharField(max_length=512)
    x = models.FloatField()
    y = models.FloatField()

    class Meta:
        db_table = 'mens_pants'
