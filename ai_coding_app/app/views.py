from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from .models import TestModel, MedicalChart, Note, ICD10Code, CodeAssignment

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from dotenv import load_dotenv
load_dotenv()

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
    
class CodeChartView(APIView):
    """
    API view to perform semantic coding on a medical chart and store results. 
    """

    def post(self, request: Request) -> Response:
        """
        Ascribes ICD-10 codes to each note in a specified chart. 

        :param request: Request object containing 'external_chart_id' and 'save' (bool).
        :return: JSON list of assigned codes and their similarity scores.
        """
        chart_id = request.data.get('external_chart_id')
        save_to_db = request.data.get('save', False)    # default = False

        # 1. Fetch notes from SQLite for this chart 
        try:
            chart = MedicalChart.objects.get(external_chart_id=chart_id)
            notes = Note.objects.filter(chart=chart) # 
        except MedicalChart.DoesNotExist:
            return Response({"error": "Chart not found"}, status=status.HTTP_404_NOT_FOUND)

        # 2. Setup Vector Store Connection
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        vector_db = Chroma(persist_directory="data/chroma_db", embedding_function=embeddings)

        results = []

        # 3. Process each note 
        for note in notes:
            # Layer 1: Find Top Cluster 
            cluster_matches = vector_db.similarity_search(
                note.content, 
                k=1, 
                filter={"type": "cluster_header"}
            )
            
            if not cluster_matches:
                continue # Skip or handle error if no cluster found

            top_cluster_id = cluster_matches[0].metadata['cluster_id']

            # Layer 2: Find Specific Code within that cluster
            code_matches = vector_db.similarity_search_with_relevance_scores(
                note.content, 
                k=1, 
                filter={
                    "$and": [
                        {"cluster_id": {"$eq": top_cluster_id}},
                        {"type": {"$eq": "specific_code"}}
                    ]
                }
            )
            
            if not code_matches:
                continue
            
            top_doc, raw_score = code_matches[0]
            # Linear shift: Maps -1 to 0 and 1 to 1. Eliminates negatives scores. 
            # This keeps the clinical signal perfectly intact while making it "pretty"
            normalized_score = (raw_score + 1) / 2
            score = round(normalized_score, 4)
            icd_code_val = top_doc.metadata['code'] # extract code

            # 4. Persistence (if save=True)
            if save_to_db:
                # Ensure the code exists in our ICD10Code table first
                icd_obj, _ = ICD10Code.objects.get_or_create(
                    code=icd_code_val,
                    defaults={'description': top_doc.page_content}
                )
                # Create the assignment
                CodeAssignment.objects.create(
                    note=note,
                    icd10_code=icd_obj,
                    similarity_score=score
                )

            results.append({
                "note_id": note.note_id,
                "icd_code": icd_code_val,
                "similarity_score": score
            })

        return Response(results, status=status.HTTP_200_OK)