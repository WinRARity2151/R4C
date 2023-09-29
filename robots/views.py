from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from datetime import datetime
from django.utils import timezone
from .models import Robot

@method_decorator(csrf_exempt, name='dispatch')
class RobotCreateView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            model = data.get('model')
            version = data.get('version')
            created = data.get('created')
            max_model_length = Robot._meta.get_field('model').max_length
            max_version_length = Robot._meta.get_field('version').max_length

            if model is None or version is None or created is None:
                return JsonResponse({'message': 'Неверные данные'}, status=400)

            if len(model) > max_model_length or len(version) > max_version_length:
                return JsonResponse({'message': 'Превышена максимальная длина полей'}, status=400)

            try:
                created_datetime = datetime.strptime(created, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return JsonResponse({'message': 'Неверный формат времени'}, status=400)

            robot = Robot(serial=model+'-'+version, model=model, version=version, created=timezone.make_aware(created_datetime))
            robot.save()

            return JsonResponse({'message': 'Запись успешно создана'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'message': 'Неверный формат JSON'}, status=400)
