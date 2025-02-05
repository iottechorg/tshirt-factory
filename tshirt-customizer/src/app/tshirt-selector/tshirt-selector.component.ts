import { Component } from '@angular/core';
import { TshirtOptions, OrderPayload, AiImageResponse } from '../models/tshirt-options.model';
import { ApiService } from '../api.service';
import { FormsModule } from '@angular/forms';
import { NgIf } from '@angular/common';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { Router } from '@angular/router';  // Import Router
import {  OnInit } from '@angular/core';
import { environment } from '../environments/environment';


@Component({
  selector: 'app-tshirt-selector',
  standalone: true,
  imports: [FormsModule, NgIf, MatFormFieldModule, MatSelectModule, MatInputModule, MatButtonModule, MatCardModule],
  templateUrl: './tshirt-selector.component.html',
  styleUrls: ['./tshirt-selector.component.css'],
})
export class TshirtSelectorComponent implements OnInit{
    tshirtOptions: TshirtOptions = {
        material: 'Cotton',
        size: 'Large',
        color: 'White',
        collar: 'circle', // Changed facet to collar with a default value
        
      };
    apiLimitReached: boolean = false;  // Added flag
    aiGeneratedImage: string = '';
    extraKeywords: string = ''; // New property for extra keywords
    apiLimitMessage: string = ''; // Added error message
    apiUrl: string | undefined;


    constructor(private apiService: ApiService, private router: Router) {}
  
    ngOnInit(): void {
      this.apiUrl = environment.apiUrl;
    }
    generateAiImage() {
        this.apiLimitReached = false; // Reset error flag

        this.apiService.generateAiImage(this.tshirtOptions, this.extraKeywords).subscribe(
             (imageUrl: string) => {
                this.aiGeneratedImage = imageUrl;
             },
             (error) => {
                console.error('Error generating AI image:', error);
                if(error.status === 429) { // Check for status code 429 (Too Many Requests)
                  this.apiLimitReached = true;
                  this.apiLimitMessage = "The API limit has been reached. Please wait a moment and try again.";
                } else {
                   this.apiLimitMessage = "Failed to generate the image. Please try again."; //Generic error
                }
            }
        )
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
        //tshirtOptions: this.tshirtOptions,
        //aiGeneratedImage: this.aiGeneratedImage,
        product_name: this.generateRandomName(),
        product_details:{
          material : this.tshirtOptions.material,
          cut_size: this.tshirtOptions.size,
          color: this.tshirtOptions.color,
          collar: this.tshirtOptions.collar,
          extraKeywords: this.extraKeywords
        }
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
      window.location.href = url;  // Use window.location.href for external URLs

    } else {
      console.error("API_URL is not defined. Cannot navigate.")
    }
  
    }
  }