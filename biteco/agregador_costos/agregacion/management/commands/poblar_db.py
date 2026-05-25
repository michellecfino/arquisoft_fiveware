from django.core.management.base import BaseCommand
from agregacion.models import Consumo, ResumenMensual
from datetime import datetime
import random
from decimal import Decimal

class Command(BaseCommand):
    help = 'Poblar base de datos usando los modelos de Django'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Poblando base de datos...")
        
        for i in range(1000):
            costo = Decimal(str(round(random.uniform(10, 5000), 2)))
            
            consumo = Consumo.objects.create(
                id_empresa=random.randint(1, 5),
                id_area=random.randint(1, 10),
                id_proyecto=random.randint(100, 120),
                nombre_servicio=random.choice(["AWS EC2", "AWS S3", "AWS Lambda"]),
                costo=costo,
                moneda="USD",
                anio=2026,
                mes=random.randint(1, 5),
                fecha_consumo=datetime.now()
            )
            
            resumen, _ = ResumenMensual.objects.get_or_create(
                id_empresa=consumo.id_empresa,
                id_area=consumo.id_area,
                id_proyecto=consumo.id_proyecto,
                anio=consumo.anio,
                mes=consumo.mes,
                defaults={'moneda': consumo.moneda}
            )
            
            resumen.costo_total += consumo.costo
            resumen.cantidad_registros += 1
            resumen.save()
            
            if (i + 1) % 100 == 0:
                self.stdout.write(f"✅ {i + 1} registros")
        
        self.stdout.write(self.style.SUCCESS("✅ Poblado completado!"))
