from django.http import JsonResponse, HttpResponse
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from datetime import datetime, timedelta
from django.utils import timezone
from openpyxl import Workbook
import tempfile
import os
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
@method_decorator(csrf_exempt, name='dispatch')
class DownloadExcelView(View):
    def get(self, request, *args, **kwargs):
        today = datetime.now()
        current_weekday = today.weekday()
        start_date = today - timedelta(days=current_weekday)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)

        robots = Robot.objects.filter(created__gte=start_date, created__lte=end_date) \
            .values('model', 'version') \
            .annotate(count=Count('id'))

        workbook = Workbook()
        default_sheet = workbook.active
        workbook.remove(default_sheet)

        unique_models = Robot.objects.filter(created__gte=start_date, created__lte=end_date).values_list('model', flat=True).distinct()
        for model in unique_models:
            model_sheet = workbook.create_sheet(title=f"Модель {model}")
            model_sheet.append(["Модель", "Версия", "Количество за неделю"])
            for data in robots.filter(model=model):
                model_sheet.append([model, data['version'], data['count']])

        excel_file = tempfile.NamedTemporaryFile(delete=False)
        workbook.save(excel_file.name)

        with open(excel_file.name, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="сводка_по_производству_роботов.xlsx"'

        excel_file.close()
        os.remove(excel_file.name)

        return response
