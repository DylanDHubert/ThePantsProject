from django.shortcuts import render
from django.http import JsonResponse
import requests


def index(request):
    return render(request, 'index.html')

def process(request):
    return JsonResponse({'message': "PLACEHOLDER"}, status=200)
    """
    if request.method == 'POST':
        print("POST TRIGGERED IN SERVER")
        try:
            response = requests.get('http://localhost:8000/process')
            return JsonResponse({'message': response.text}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    """
