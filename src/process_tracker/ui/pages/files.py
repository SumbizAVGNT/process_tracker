from __future__ import annotations
import flet as ft
from ..components.shell import page_scaffold
from ..components.forms import async_button, toast
from ..services.api import api


def view(page: ft.Page) -> ft.View:
    title = ft.Text("Файлы", size=22, weight="w700")
    picked = ft.Text("Файлы не выбраны")
    result = ft.Text()
    fp = ft.FilePicker()
    page.overlay.append(fp)

    files: list[tuple[str, bytes]] = []

    def _on_pick(e: ft.FilePickerResultEvent):
        nonlocal files
        files = []
        if e.files:
            picked.value = ", ".join([f.name for f in e.files])
            for f in e.files:
                try:
                    with open(f.path, "rb") as fh:
                        files.append((f.name, fh.read()))
                except Exception:
                    pass
        else:
            picked.value = "Файлы не выбраны"
        page.update()

    fp.on_result = _on_pick

    async def _upload():
        if not files:
            toast(page, "Выберите файлы", kind="warning")
            return
        res = await api.files_upload(files)
        result.value = str(res)
        toast(page, "Загружено", kind="success")
        page.update()

    body = ft.Column(
        [
            title,
            ft.Row(
                [
                    ft.ElevatedButton("Выбрать файлы", icon=ft.icons.UPLOAD_FILE, on_click=lambda _e: fp.pick_files(allow_multiple=True)),
                    async_button(page, "Загрузить", icon=ft.icons.CLOUD_UPLOAD, task_factory=_upload),
                    picked,
                ],
                spacing=10,
            ),
            ft.Divider(opacity=0.06),
            result,
        ],
        spacing=10,
        expand=True,
    )

    return page_scaffold(page, title="Файлы", route="/files", body=body)
