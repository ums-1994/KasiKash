import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FinancialAdvisor } from './financial-advisor';

describe('FinancialAdvisor', () => {
  let component: FinancialAdvisor;
  let fixture: ComponentFixture<FinancialAdvisor>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FinancialAdvisor]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FinancialAdvisor);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
