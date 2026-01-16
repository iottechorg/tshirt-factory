import { Component } from '@angular/core';
import { ProductCreatorComponent } from './product-creator/product-creator.component';
@Component({
  selector: 'app-root',
  imports: [ProductCreatorComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'Custom Product Designer';
}