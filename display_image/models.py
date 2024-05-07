from django.db import models


class File(models.Model):
    '''
    this models represent the html file that needed to be diplayed
    '''
    name = models.CharField(max_length=225, primary_key=True)
    # parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    # is_folder = models.BooleanField(default=False)
    path = models.TextField(null=True, blank=True)
    value = models.CharField(max_length=225)
    html = models.TextField() # null value set to ''
    row = models.CharField(max_length=225)
    col = models.CharField(max_length=225)
    
    def __str__(self):
        return str(self.name)
