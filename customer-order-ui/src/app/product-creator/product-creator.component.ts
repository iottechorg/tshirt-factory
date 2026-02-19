import { Component } from '@angular/core';
import { ProductOptions, OrderPayload, AiImageResponse } from '../models/product-options.model';
import { ApiService } from '../api.service';
import { FactoryConfigService } from '../factory-config.service';
import { FormsModule } from '@angular/forms';
import { NgIf, NgFor, NgClass } from '@angular/common';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { Router } from '@angular/router';
import { OnInit } from '@angular/core';
import { environment } from '../environments/environment';

@Component({
  selector: 'app-product-creator',
  standalone: true,
  imports: [FormsModule, NgIf, NgFor, NgClass, MatFormFieldModule, MatSelectModule, MatInputModule, MatButtonModule, MatCardModule],
  templateUrl: './product-creator.component.html',
  styleUrls: ['./product-creator.component.css'],
})
export class ProductCreatorComponent implements OnInit {
  productOptions: ProductOptions = {
    description: '',
    quantity: 1,
  };

  apiLimitReached: boolean = false;
  aiGeneratedImage: string = '';
  apiLimitMessage: string = '';
  isGenerating: boolean = false;
  isImageLoading: boolean = false;
  apiUrl: string | undefined;
  
  // Mirror backend retry/backoff settings for user information
  readonly retryIntervals: number[] = [2, 4, 8, 16, 32]; // seconds between retries (backoff)
  readonly retryBackoffFactor: number = 2;
  readonly retryTotal: number = 5; // number of retries configured on backend
  readonly attemptTimeout: number = 60; // per-attempt timeout in seconds on backend

  // Estimated worst-case wait: (initial attempt + retries) * timeout + sum(backoff intervals)
  get estimatedWorstCaseSeconds(): number {
    const attempts = 1 + this.retryTotal;
    const backoffSum = this.retryIntervals.reduce((a, b) => a + b, 0);
    return attempts * this.attemptTimeout + backoffSum;
  }

  get estimatedWorstCaseDisplay(): string {
    const s = this.estimatedWorstCaseSeconds;
    if (s >= 60) {
      const m = Math.floor(s / 60);
      const sec = Math.round(s % 60);
      return `${m} min ${sec} s`;
    }
    return `${Math.round(s)} s`;
  }

  constructor(private apiService: ApiService, private router: Router, private cfgService: FactoryConfigService) {}

  ngOnInit(): void {
    this.apiUrl = environment.apiUrl;
  }

  generateAiImage() {
    // Immediate disabling check - ignore if already generating
    if (this.isGenerating || !this.productOptions.description.trim()) {
      console.log('Generate AI Image ignored: already generating or empty description');
      return;
    }

    // Set state immediately to prevent any further clicks
    this.isGenerating = true;
    this.apiLimitReached = false;
    this.apiLimitMessage = '';
    this.aiGeneratedImage = '';
    this.isImageLoading = false;

    console.log('Generate AI Image starting...');
    console.log('Product description:', this.productOptions.description);

    this.apiService.generateAiImage(this.productOptions.description).subscribe({
      next: (imageUrl: string) => {
        console.log('Generated image URL acquired:', imageUrl);
        this.aiGeneratedImage = imageUrl;
        // Keep `isGenerating = true` until the image has actually loaded
        // so the Generate button remains disabled while the preview is being fetched/loaded.
        this.isImageLoading = true; // Show loading spinner while image loads
      },
      error: (error: any) => {
        console.error('Error initiating AI image generation:', error);
        // On error, re-enable the button and clear loading state
        this.isGenerating = false;
        this.isImageLoading = false;
        if (error.status === 429) {
          this.apiLimitReached = true;
          this.apiLimitMessage = 'API rate limit reached. Please wait a moment and try again.';
        } else {
          this.apiLimitMessage = 'Failed to generate the design. Please try again.';
        }
      }
    });
  }

  generateRandomName = () => {
    const adjectives = ['Custom', 'Unique', 'Special', 'Premium', 'Exclusive', 'Handcrafted', 'Artisan', 'Bespoke', 'Personalized', 'Tailored'];
    const nouns = ['Product', 'Item', 'Creation', 'Design', 'Piece', 'Article', 'Object', 'Artifact', 'Work', 'Masterpiece'];
    const descriptors = ['Edition', 'Series', 'Collection', 'Line', 'Range', 'Set', 'Group', 'Batch', 'Lot', 'Assortment'];

    const randomAdjective = adjectives[Math.floor(Math.random() * adjectives.length)];
    const randomNoun = nouns[Math.floor(Math.random() * nouns.length)];
    const randomDescriptor = descriptors[Math.floor(Math.random() * descriptors.length)];

    return `${randomAdjective} ${randomNoun} ${randomDescriptor}`;
  };

  placeOrder() {
    const order: OrderPayload = {
      product_name: this.generateRandomName(),
      product_details: {
        description: this.productOptions.description,
      },
      quantity: this.productOptions.quantity || 1,
    };
    console.log(order);
    this.apiService.placeOrder(order).subscribe({
      next: (response: any) => {
        console.log('Order placed successfully:', response);
      },
      error: (error: any) => {
        console.error('Error placing order:', error);
      },
    });
  }

  navigateToMachineObservation() {
    if (this.apiUrl) {
      const url = `${this.apiUrl}`;
      window.location.href = url;
    }
  }

  onImageLoadSuccess() {
    console.log('AI-generated image loaded successfully');
    // Image finished loading: clear loading state and re-enable Generate button
    this.isImageLoading = false;
    this.isGenerating = false;
  }

  onImageLoadError() {
    console.error('Failed to load AI-generated image');
    // Loading failed: clear loading state and re-enable Generate button
    this.isImageLoading = false;
    this.isGenerating = false;
    this.apiLimitMessage = 'Image failed to load. The design service may be temporarily unavailable.';
    this.aiGeneratedImage = ''; // Clear the broken image
  }
}