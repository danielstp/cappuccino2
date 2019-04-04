import { Materia  } from './materia';
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class MateriaService {

  private baseUrl = 'http://localhost:8000/api/v1/materias/';

  getListaMaterias(): Observable<any> {
    return this.http.get(`${this.baseUrl}`);
  }

  getMateria(codigo: number): Observable<any> {
    return this.http.get(`${this.baseUrl}${codigo}`);
  }

  constructor(private http: HttpClient) { }


}
