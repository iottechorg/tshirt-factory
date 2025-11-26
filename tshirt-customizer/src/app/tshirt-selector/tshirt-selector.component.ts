import { Component } from '@angular/core';
import { TshirtOptions, OrderPayload, AiImageResponse } from '../models/tshirt-options.model';
import { ApiService } from '../api.service';
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

interface ColorOption {
  name: string;
  hex: string;
}

interface CollarOption {
  value: string;
  label: string;
}

@Component({
  selector: 'app-tshirt-selector',
  standalone: true,
  imports: [FormsModule, NgIf, NgFor, NgClass, MatFormFieldModule, MatSelectModule, MatInputModule, MatButtonModule, MatCardModule],
  templateUrl: './tshirt-selector.component.html',
  styleUrls: ['./tshirt-selector.component.css'],
})
export class TshirtSelectorComponent implements OnInit {
  tshirtOptions: TshirtOptions = {
    material: 'Cotton',
    size: 'Medium',
    color: 'White',
    collar: 'circle',
  };

  // New design data
  materials: string[] = ['Cotton', 'Polyester', 'Blend'];
  sizes: string[] = ['Small', 'Medium', 'Large', 'X-Large'];
  colors: ColorOption[] = [
    { name: 'White', hex: '#ffffff' },
    { name: 'Black', hex: '#000000' },
    { name: 'Red', hex: '#ef4444' },
    { name: 'Blue', hex: '#3b82f6' },
    { name: 'Green', hex: '#10b981' },
    { name: 'Navy', hex: '#001f3f' },
    { name: 'Gray', hex: '#6b7280' },
    { name: 'Charcoal', hex: '#1f2937' },
  ];
  collars: CollarOption[] = [
    { value: 'circle', label: 'Crew' },
    { value: 'v-shape', label: 'V-Neck' },
    { value: 'polo', label: 'Polo' },
  ];

  selectedColor: ColorOption = this.colors[0];
  apiLimitReached: boolean = false;
  aiGeneratedImage: string = '';
  extraKeywords: string = '';
  apiLimitMessage: string = '';
  isGenerating: boolean = false;
  apiUrl: string | undefined;

  constructor(private apiService: ApiService, private router: Router) {}

  ngOnInit(): void {
    this.apiUrl = environment.apiUrl;
  }

  generateAiImage() {
    console.log('Generate AI Image clicked!');
    console.log('T-shirt options:', this.tshirtOptions);
    console.log('Selected color:', this.selectedColor);
    console.log('Extra keywords:', this.extraKeywords);
    
    this.isGenerating = true;
    this.apiLimitReached = false;
    this.apiLimitMessage = '';

    // Update tshirtOptions.color with the selected color name
    this.tshirtOptions.color = this.selectedColor.name;

    this.apiService.generateAiImage(this.tshirtOptions, this.extraKeywords).subscribe(
      (imageUrl: string) => {
        console.log('Generated image URL:', imageUrl);
        this.aiGeneratedImage = imageUrl;
        this.isGenerating = false;
      },
      (error) => {
        console.error('Error generating AI image:', error);
        this.isGenerating = false;
        if (error.status === 429) {
          this.apiLimitReached = true;
          this.apiLimitMessage = 'API rate limit reached. Please wait a moment and try again.';
        } else {
          this.apiLimitMessage = 'Failed to generate the design. Please try again.';
        }
      }
    );
  }

  generateRandomName = () => {
    const adjectives = ['Stylish', 'Cool', 'Comfy', 'Trendy', 'Classic', 'Vibrant', 'Sleek', 'Casual', 'Modern', 'Bold'];
    const nouns = ['Tee', 'Shirt', 'Top', 'Outfit', 'Apparel', 'Wear', 'Garment', 'Attire', 'Design', 'Piece'];
    const descriptors = ['Deluxe', 'Edition', 'Line', 'Pro', 'Series', 'Vibe', 'Edge', 'Collection', 'Fit', 'Style'];

    const randomAdjective = adjectives[Math.floor(Math.random() * adjectives.length)];
    const randomNoun = nouns[Math.floor(Math.random() * nouns.length)];
    const randomDescriptor = descriptors[Math.floor(Math.random() * descriptors.length)];

    return `${randomAdjective} ${randomNoun} ${randomDescriptor}`;
  };

  placeOrder() {
    const order: OrderPayload = {
      product_name: this.generateRandomName(),
      product_details: {
        material: this.tshirtOptions.material,
        cut_size: this.tshirtOptions.size,
        color: this.tshirtOptions.color,
        collar: this.tshirtOptions.collar,
        extraKeywords: this.extraKeywords,
      },
    };
    console.log(order);
    this.apiService.placeOrder(order).subscribe({
      next: (response) => {
        console.log('Order placed successfully:', response);
      },
      error: (error) => {
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

  onImageLoadError() {
    console.error('Failed to load AI-generated image');
    this.apiLimitMessage = 'Image failed to load. The design service may be temporarily unavailable.';
    this.aiGeneratedImage = ''; // Clear the broken image
  }
}