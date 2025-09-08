import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-contributions',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="contributions-page">
      <div class="page-background"></div>
      <div class="page-overlay"></div>
      
    <div class="contributions-container">
      <div class="header">
        <h1>Contributions</h1>
          <button class="btn-primary" (click)="openModal()">
            <i class="fas fa-plus"></i> Make New Contribution
          </button>
      </div>
      
      <div class="summary-cards">
        <div class="summary-card">
            <div class="card-icon">
              <i class="fas fa-piggy-bank"></i>
            </div>
          <h3>Total Contributed</h3>
          <p class="amount">R{{ totalContributed }}</p>
        </div>
        <div class="summary-card">
            <div class="card-icon">
              <i class="fas fa-calendar-month"></i>
            </div>
          <h3>This Month</h3>
          <p class="amount">R{{ thisMonthContribution }}</p>
        </div>
        <div class="summary-card">
            <div class="card-icon">
              <i class="fas fa-clock"></i>
            </div>
          <h3>Next Due</h3>
          <p class="date">{{ nextDueDate }}</p>
        </div>
      </div>
      
      <div class="contributions-list">
        <h2>Recent Contributions</h2>
          <div class="contributions-grid">
        <div class="contribution-item" *ngFor="let contribution of contributions">
              <div class="contribution-header">
                <div class="stokvel-info">
                  <i class="fas fa-users"></i>
            <span class="stokvel-name">{{ contribution.stokvelName }}</span>
                </div>
            <span class="amount">R{{ contribution.amount }}</span>
          </div>
          <div class="contribution-meta">
                <div class="meta-item">
                  <i class="fas fa-calendar"></i>
            <span class="date">{{ contribution.date }}</span>
                </div>
                <div class="meta-item">
                  <i class="fas fa-credit-card"></i>
                  <span class="method">{{ contribution.method }}</span>
                </div>
            <span class="status" [class]="contribution.status">{{ contribution.status }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Contribution Modal -->
      <div class="modal-overlay" *ngIf="showModal" (click)="closeModal()">
        <div class="modal-content" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <h3>New Contribution</h3>
            <button class="close-btn" (click)="closeModal()">×</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>Stokvel</label>
              <select class="form-control" [(ngModel)]="form.stokvelId">
                <option value="">Select...</option>
                <option *ngFor="let s of stokvels" [value]="s.id">{{ s.name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Amount (R)</label>
              <input type="number" class="form-control" [(ngModel)]="form.amount" />
            </div>
            <div class="form-group">
              <label>Payment Method</label>
              <select class="form-control" [(ngModel)]="form.method">
                <option value="bank">Bank Transfer</option>
                <option value="card">Card</option>
                <option value="mobile">Mobile Money</option>
              </select>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" (click)="closeModal()">Cancel</button>
            <button class="btn-primary" [disabled]="!form.stokvelId || !form.amount" (click)="submit()">Submit</button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .contributions-page {
      position: relative;
      min-height: 100vh;
    }
    
    .contributions-container { 
      padding: 2rem; 
      position: relative;
      z-index: 1;
    }
    
    .header { 
      display: flex; 
      justify-content: space-between; 
      align-items: center; 
      margin-bottom: 2rem; 
      flex-wrap: wrap;
      gap: 1rem;
    }
    
    .header h1 { 
      color: #1a1a1a;
      text-shadow: 0 1px 3px rgba(255, 255, 255, 0.8);
      font-size: 2.5rem;
      font-weight: 800;
    }
    
    .btn-primary { 
      background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); 
      color: white; 
      border: none; 
      padding: 0.75rem 1.5rem; 
      border-radius: 0.75rem; 
      cursor: pointer; 
      font-weight: 600;
      box-shadow: 0 4px 15px rgba(46, 139, 87, 0.3);
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    
    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(46, 139, 87, 0.4);
    }
    
    .summary-cards { 
      display: grid; 
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
      gap: 2rem; 
      margin-bottom: 3rem; 
    }
    
    .summary-card { 
      background: rgba(255, 255, 255, 0.95); 
      border: 1px solid rgba(255, 255, 255, 0.3); 
      border-radius: 1.5rem; 
      padding: 2rem; 
      text-align: center; 
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      backdrop-filter: blur(20px);
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }
    
    .summary-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .card-icon {
      width: 60px;
      height: 60px;
      background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 1rem;
      box-shadow: 0 4px 15px rgba(46, 139, 87, 0.3);
    }
    
    .card-icon i {
      font-size: 1.5rem;
      color: white;
    }
    
    .summary-card h3 { 
      color: #2b2b2b; 
      font-size: 1rem; 
      margin-bottom: 1rem; 
      font-weight: 600;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .summary-card .amount { 
      font-size: 2.5rem; 
      font-weight: 800; 
      color: var(--primary-color); 
      text-shadow: 0 2px 4px rgba(46, 139, 87, 0.3);
    }
    
    .summary-card .date { 
      font-size: 1.5rem; 
      font-weight: 700; 
      color: var(--primary-color); 
      text-shadow: 0 2px 4px rgba(46, 139, 87, 0.3);
    }
    
    .contributions-list h2 { 
      color: #1a1a1a; 
      margin-bottom: 2rem; 
      font-size: 2rem;
      font-weight: 700;
      text-shadow: 0 1px 3px rgba(255, 255, 255, 0.8);
    }
    
    .contributions-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
      gap: 1.5rem;
    }
    
    .contribution-item { 
      background: rgba(255, 255, 255, 0.95); 
      border: 1px solid rgba(255, 255, 255, 0.3); 
      border-radius: 1rem; 
      padding: 1.5rem; 
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      backdrop-filter: blur(20px);
      transition: all 0.3s ease;
    }
    
    .contribution-item:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .contribution-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }
    
    .stokvel-info {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    
    .stokvel-info i {
      color: var(--primary-color);
      font-size: 1.2rem;
    }
    
    .stokvel-name { 
      color: #1a1a1a; 
      font-weight: 700; 
      font-size: 1.1rem;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .amount { 
      color: var(--primary-color); 
      font-weight: 800; 
      font-size: 1.5rem;
      text-shadow: 0 2px 4px rgba(46, 139, 87, 0.3);
    }
    
    .contribution-meta { 
      display: flex; 
      justify-content: space-between; 
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }
    
    .meta-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: #2b2b2b;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .meta-item i {
      color: var(--secondary-color);
      font-size: 0.9rem;
    }
    
    .date { 
      color: #2b2b2b; 
      font-size: 0.9rem; 
      font-weight: 500;
    }
    
    .method {
      color: #2b2b2b;
      font-size: 0.9rem;
      font-weight: 500;
      text-transform: capitalize;
    }
    
    .status { 
      padding: 0.375rem 0.75rem; 
      border-radius: 0.5rem; 
      font-size: 0.75rem; 
      font-weight: 600;
      text-transform: uppercase;
    }
    
    .status.completed { 
      background: rgba(46, 139, 87, 0.2); 
      color: var(--success-color); 
      border: 1px solid rgba(46, 139, 87, 0.3);
    }
    
    .status.pending {
      background: rgba(245, 166, 35, 0.2);
      color: var(--warning-color);
      border: 1px solid rgba(245, 166, 35, 0.3);
    }
    
    /* Modal styles */
    .modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      backdrop-filter: blur(10px);
    }
    
    .modal-content {
      background: rgba(255, 255, 255, 0.98);
      border: 1px solid rgba(255, 255, 255, 0.3);
      border-radius: 1.5rem;
      width: 90%;
      max-width: 500px;
      overflow: hidden;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
      backdrop-filter: blur(20px);
    }
    
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.5rem 2rem;
      border-bottom: 1px solid rgba(0, 0, 0, 0.1);
    }
    
    .modal-body {
      padding: 1.5rem 2rem;
    }
    
    .modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: 1rem;
      padding: 1.5rem 2rem;
      border-top: 1px solid rgba(0, 0, 0, 0.1);
    }
    
    .close-btn {
      background: none;
      border: none;
      color: #6b7280;
      font-size: 1.5rem;
      cursor: pointer;
      transition: color 0.3s ease;
    }
    
    .close-btn:hover {
      color: #374151;
    }
    
    .form-group {
      margin-bottom: 1.5rem;
    }
    
    .form-control {
      width: 100%;
      padding: 0.75rem 1rem;
      background: rgba(255, 255, 255, 0.9);
      border: 1px solid rgba(0, 0, 0, 0.1);
      border-radius: 0.75rem;
      color: #1a1a1a;
      font-size: 1rem;
      transition: all 0.3s ease;
    }
    
    .form-control:focus {
      outline: none;
      border-color: var(--primary-color);
      box-shadow: 0 0 0 3px rgba(46, 139, 87, 0.1);
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
      .contributions-container {
        padding: 1rem;
      }
      
      .header {
        flex-direction: column;
        align-items: stretch;
        text-align: center;
      }
      
      .header h1 {
        font-size: 2rem;
        margin-bottom: 1rem;
      }
      
      .summary-cards {
        grid-template-columns: 1fr;
        gap: 1.5rem;
      }
      
      .contributions-grid {
        grid-template-columns: 1fr;
      }
      
      .contribution-meta {
        flex-direction: column;
        align-items: flex-start;
      }
    }
  `]
})
export class ContributionsPage {
  totalContributed = 8500;
  thisMonthContribution = 1500;
  nextDueDate = '15 Dec 2024';
  
  stokvels: any[] = [];
  contributions: any[] = [];

  showModal = false;
  form = { stokvelId: '', amount: 0, method: 'bank' } as any;

  constructor(private api: ApiService) {
    this.stokvels = this.api.getStokvels();
    this.contributions = this.api.getContributions();
  }

  openModal() { this.showModal = true; }
  closeModal() { this.showModal = false; this.form = { stokvelId: '', amount: 0, method: 'bank' }; }
  submit() {
    const c = this.api.addContribution(this.form);
    this.contributions = [...this.api.getContributions()];
    this.totalContributed += c.amount;
    this.thisMonthContribution += c.amount;
    this.closeModal();
    alert('Contribution recorded');
  }
} 