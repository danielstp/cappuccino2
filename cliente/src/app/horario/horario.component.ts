import { Component, OnInit } from '@angular/core';
import { Car } from './domain/car';
import { CarService } from './service/carservice';
import { TableModule } from 'primeng/table';

@Component({
  selector: 'app-horario',
  templateUrl: './horario.component.html',
  styleUrls: ['./horario.component.styl']
})
export class HorarioComponent implements OnInit {

    cars: Car[];

    cols: any[];

    constructor(private carService: CarService) { }

    ngOnInit() {
        this.carService.getCarsSmall().then(cars => this.cars = cars);

        this.cols = [
            { field: 'vin', header: 'Hora' },
            { field: 'year', header: 'Lunes' },
            { field: 'brand', header: 'Martes' },
            { field: 'color', header: 'Miercoles' },
            { field: 'jueves', header: 'Jueves'},
            { filed: 'viernes', header: 'Viernes'},
            { filed: 'sabado', header: 'Sabado'}
        ];
    }
}
