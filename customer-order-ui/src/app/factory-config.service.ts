import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class FactoryConfigService {
  private baseUrl = 'http://127.0.0.1:5001';

  constructor(private http: HttpClient) { }

  getRuntimeConfig(): Observable<any> {
    return this.http.get(`${this.baseUrl}/factory-config`);
  }

  getGeneratedConfig(factoryId: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/factory-config/generated/${factoryId}`);
  }
}
