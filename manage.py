#!/usr/bin/env python
"""manage.py — Django management utility."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. Asegúrese de que esté instalado y que "
            "el virtualenv esté activado."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
