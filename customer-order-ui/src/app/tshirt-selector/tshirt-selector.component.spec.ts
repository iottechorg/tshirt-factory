import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TshirtSelectorComponent } from './tshirt-selector.component';

describe('TshirtSelectorComponent', () => {
  let component: TshirtSelectorComponent;
  let fixture: ComponentFixture<TshirtSelectorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TshirtSelectorComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TshirtSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
