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

    getFactoryConfig() {
        return this.http.get(this.orderUrl + '/factory-config');
    }

    generateAiImage(tshirtOptions: any, extraKeywords:string): Observable<any> {
        let keywords =  `${tshirtOptions.color}_${tshirtOptions.collar}_tshirt`
        if(extraKeywords)
            keywords = `${keywords}_${extraKeywords.trim().replace(/\s+/g, '_')}`;

        // Use the AI image generation service with the constructed prompt
        const prompt = keywords.replace(/_/g, ' ');
        const imageUrl = `${this.aiImageUrl}${encodeURIComponent(prompt)}`;

        console.log('API Service: Generating AI image');
        console.log('Keywords:', keywords);
        console.log('Prompt:', prompt);
        console.log('Using image URL:', imageUrl);

        return new Observable<string>(observer => {
            observer.next(imageUrl);
            observer.complete();
        });
    }

    placeOrder(order: OrderPayload): Observable<any> {        
        return this.http.post(this.orderUrl+"/production", order);
    }
}