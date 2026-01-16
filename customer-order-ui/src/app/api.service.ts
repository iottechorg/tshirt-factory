import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, Observer } from 'rxjs';
import { OrderPayload } from './models/product-options.model';
import { environment } from './environments/environment';

@Injectable({
    providedIn: 'root',
})
export class ApiService {
    private aiImageUrl = 'https://image.pollinations.ai/prompt/';
    private orderUrl = environment.apiUrl;

    constructor(private http: HttpClient) { }

    getFactoryConfig() {
        return this.http.get(this.orderUrl + '/factory-config');
    }

    generateAiImage(description: string): Observable<string> {
        if (!description || description.trim().length === 0) {
            throw new Error('Description cannot be empty');
        }

        // Use backend proxy to fetch from pollinations.ai (avoids 403 hotlink protection)
        const prompt = description.trim();
        // Add cache-busting parameter to ensure new images aren't cached
        const cacheBuster = Date.now();
        const proxyUrl = `${this.orderUrl}/proxy-image?prompt=${encodeURIComponent(prompt)}&width=512&height=512&_t=${cacheBuster}`;

        console.log('API Service: Generating AI image via backend proxy');
        console.log('Description:', description);
        console.log('Prompt:', prompt);
        console.log('Proxy URL:', proxyUrl);

        return new Observable<string>((observer: Observer<string>) => {
            observer.next(proxyUrl);
            observer.complete();
        });
    }

    placeOrder(order: OrderPayload): Observable<any> {
        if (!order) {
            throw new Error('Order payload cannot be null or undefined');
        }

        const headers = new HttpHeaders({
            'Content-Type': 'application/json'
        });

        console.log('API Service: Placing order to', this.orderUrl + '/production');
        console.log('Order payload:', order);

        return this.http.post(this.orderUrl + '/production', order, { headers });
    }
}