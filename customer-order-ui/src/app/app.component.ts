import { Component } from '@angular/core';
import { TshirtSelectorComponent } from './tshirt-selector/tshirt-selector.component';
@Component({
  selector: 'app-root',
  imports: [TshirtSelectorComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'tshirt-customizer';
}