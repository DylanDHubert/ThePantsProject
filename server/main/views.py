from django.shortcuts import render
from django.http import JsonResponse
import requests

def index(request):
    return render(request, 'index.html')

def process(request):
    if request.method == 'POST':
        try:
            response = requests.get('http://process:8080')
            return JsonResponse({'message': response.text}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)