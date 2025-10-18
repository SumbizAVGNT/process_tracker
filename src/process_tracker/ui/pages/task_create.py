# пример: src/process_tracker/ui/pages/task_create.py
import flet as ft
import httpx

from ...core.forms.schemas import FormSchema
from ..components.dynamic_form import DynamicForm

def view(page: ft.Page) -> ft.View:
    async def load_schema() -> FormSchema:
        # можно и без сети, если FormsService отдаёт in-memory
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8787") as xc:
            r = await xc.get("/api/forms/task.create")
            r.raise_for_status()
            return FormSchema.model_validate(r.json())

    async def on_submit(data: dict):
        # TODO: отправить данные на API задач
        print("submit:", data)
        page.snack_bar = ft.SnackBar(ft.Text("Задача создана"), open=True)
        page.update()

    # грузим схему лениво; для примера синхронно можно просто FormsService() использовать
    # schema = await load_schema()  # в реальном коде обернуть в run_task
    # пока используем статически — если импорт доступен:
    from ...services.forms_service import FormsService
    svc = FormsService()
    schema = svc._forms["task.create"]  # demo

    form = DynamicForm(schema, on_submit=on_submit)
    return ft.View("/tasks/create", controls=[ft.Container(form, padding=16, expand=True)])
