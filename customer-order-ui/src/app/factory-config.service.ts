import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from './environments/environment';

@Injectable({
  providedIn: 'root'
})
export class FactoryConfigService {
  private baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  getRuntimeConfig(): Observable<any> {
    return this.http.get(`${this.baseUrl}/factory-config`);
  }

  getGeneratedConfig(factoryId: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/factory-config/generated/${factoryId}`);
  }
}
