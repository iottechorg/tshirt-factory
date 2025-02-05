import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { OrderPayload } from './models/tshirt-options.model';

@Injectable({
    providedIn: 'root',
})
export class ApiService {
    //private orderUrl = environment.apiUrl; // Using env variable here
    private aiImageUrl = 'https://image.pollinations.ai/prompt/';
    private orderUrl = 'http://127.0.0.1:5001';

    constructor(private http: HttpClient) { }

    generateAiImage(tshirtOptions: any, extraKeywords:string): Observable<any> {
        let keywords =  `${tshirtOptions.color}_${tshirtOptions.collar}_tshirt`
        if(extraKeywords)
            keywords = `${keywords}_${extraKeywords.trim().replace(/\s+/g, '_')}`;

        const imageUrl = `${this.aiImageUrl}${keywords}_on_tshirt_with_white_background`;

        return new Observable<string>(observer => {
            observer.next(imageUrl);
            observer.complete();
        });
    }

    placeOrder(order: OrderPayload): Observable<any> {        
        return this.http.post(this.orderUrl+"/production", order);
    }
}