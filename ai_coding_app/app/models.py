from django.db import models

#### #! DO NOT MODIFY THIS CODE #! ####

class TestModel(models.Model):
    """
    This is a test model for the app. An example record has been created in the native SQLite database.

    Attributes:
        field1 (str): A string field
        field2 (int): An integer field
    """

    field1 = models.CharField(max_length=100)
    field2 = models.IntegerField()

    def __str__(self) -> str:
        f"""
        Return the string representation of the model instance.

        :return: The string representation of the model instance.
        :rtype: str
        """
        return self.field1
    
    def to_dict(self) -> dict:
        f"""
        Convert the model instance to a dictionary for JSON serialization.

        :return: The dictionary representation of the model instance.
        :rtype: dict
        """
        return {
            'id': self.id,
            'field1': self.field1,
            'field2': self.field2,
        }
    
#### #! END OF DO NOT MODIFY THIS CODE #! ####

# Create your models here.

class MedicalChart(models.Model):
    """
    Represents a single patient visit or medical record file.

    Attributes:
        external_chart_id (str): A unique string identifier for this medical chart
        created_at (date time): A medical chart creation timestamp
    """

    external_chart_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        f"""
        Return the string representation of the model instance.

        :return: The string representation of the model instance.
        :rtype: str
        """
        return self.external_chart_id
    
    def to_dict(self) -> dict:
        f"""
        Convert the model instance to a dictionary for JSON serialization.

        :return: The dictionary representation of the model instance.
        :rtype: dict
        """
        return {
            'external_chart_id': self.external_chart_id,
            'created_at': self.created_at,
        }
    
class Note(models.Model):
    """
    Represents an individual section within a medical chart.

    Attributes:
        chart (MedicalChart): The foreign key relationship to the parent MedicalChart instance
        note_id (str): A unique string identifier for the specific note (e.g., 'note-hpi-case12')
        title (str): The category or section title of the note, typically in all caps (e.g., 'HPI')
        content (str): The full text documented by the healthcare provider for this specific note
    """

    chart = models.ForeignKey(MedicalChart, related_name='notes', on_delete=models.CASCADE)
    note_id = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    content = models.TextField()

    def __str__(self) -> str:
        f"""
        Return the string representation of the model instance.

        :return: The string representation of the model instance.
        :rtype: str
        """
        return self.note_id
    
    def to_dict(self) -> dict:
        f"""
        Convert the model instance to a dictionary for JSON serialization.

        :return: The dictionary representation of the model instance.
        :rtype: dict
        """
        return {
            'chart': self.chart,
            'note_id': self.note_id,
            'title': self.title,
            'content': self.content,
        }