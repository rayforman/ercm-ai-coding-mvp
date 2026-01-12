from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from .models import TestModel, MedicalChart, Note

#### #! DO NOT MODIFY THIS CODE #! ####

class TestView(APIView):
    """
    This is a test view for the app. It returns a list of all the records in the TestModel.
    """

    def get(self, request: Request) -> Response :
        f"""
        Get all the records from the TestModel and return them as a list of dictionaries.

        :param request: The HTTP request object.

        :return: A JSON response containing the list of records.
        :rtype: Response
        """
        records = TestModel.objects.all()
        return Response([record.to_dict() for record in records], status=status.HTTP_200_OK)

#### #! END OF DO NOT MODIFY THIS CODE #! ####

# Create your views here.

class ChartSchemaView(APIView):
    """
    API view to return the schema of the medical charts as stored in the database.
    """

    def get(self, request: Request) -> Response:
        """
        Return the schema definition for MedicalChart and Note models.

        :param request: The HTTP request object.

        :return: A JSON response containing the database schema.
        :rtype: Response
        """
        # Hardcoded schema representation
        schema = {
            "MedicalChart": {
                "external_chart_id": "CharField (unique)",
                "created_at": "DateTimeField"
            },
            "Note": {
                "note_id": "CharField (unique)",
                "title": "CharField",
                "content": "TextField",
                "chart": "ForeignKey (MedicalChart)"
            }
        }
        return Response(schema, status=status.HTTP_200_OK)

class UploadChartView(APIView):
    """
    API view to handle the idempotent upload of medical charts and their notes.
    """

    def post(self, request: Request) -> Response:
        """
        Receive chart JSON and store it in the SQLite database idempotently.

        :param request: The HTTP request object containing chart and note data.

        :return: A JSON response with success message and total count of items.
        :rtype: Response
        """
        data = request.data
        external_chart_id = data.get('external_chart_id')

        # Idempotently get or create the parent chart
        chart, _ = MedicalChart.objects.get_or_create(
            external_chart_id=external_chart_id
        )

        # Idempotently update or create each note
        for note_data in data.get('notes', []):
            Note.objects.update_or_create(
                note_id=note_data.get('note_id'),
                defaults={
                    'chart': chart,
                    'title': note_data.get('title'),
                    'content': note_data.get('content'),
                }
            )

        return Response({
            "message": "Successfully uploaded chart to SQLite database!",
            "count": Note.objects.count()
        }, status=status.HTTP_201_CREATED)

class ListChartsView(APIView):
    """
    API view to list all charts and their associated notes.
    """

    def get(self, request: Request) -> Response:
        """
        Retrieve all charts stored in the database.

        :param request: The HTTP request object.
        
        :return: A JSON response containing all chart records.
        :rtype: Response
        """
        charts = MedicalChart.objects.all()
        output = []
        for chart in charts:
            notes = Note.objects.filter(chart=chart)
            output.append({
                "external_chart_id": chart.external_chart_id,
                "notes": [
                    {
                        "note_id": n.note_id,
                        "title": n.title,
                        "content": n.content
                    } for n in notes
                ]
            })
        return Response(output, status=status.HTTP_200_OK)