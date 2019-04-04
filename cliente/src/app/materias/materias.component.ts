import { Component, OnInit } from '@angular/core';
import { Materia } from '../materia';

@Component({
  selector: 'app-materias',
  templateUrl: './materias.component.html',
  styleUrls: ['./materias.component.styl']
})

export class MateriasComponent implements OnInit {
  materia: Materia = {
    nombre: 'Alimentos',
    código: 6969
  };

  constructor() {}

  ngOnInit() {

  }
}
