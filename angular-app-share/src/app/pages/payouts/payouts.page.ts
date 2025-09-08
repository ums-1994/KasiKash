import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-payouts',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="payouts-page">
      <div class="page-background"></div>
      <div class="page-overlay"></div>
      
      <div class="payouts-container">
        <div class="header">
          <h1>Payouts</h1>
          <button class="btn-primary" (click)="openRequestModal()">
            <i class="fas fa-plus"></i> Request Payout
          </button>
        </div>
        
        <div class="summary-cards">
          <div class="summary-card">
            <div class="card-icon">
              <i class="fas fa-wallet"></i>
            </div>
            <h3>Total Payouts</h3>
            <p class="amount">R{{ totalPayouts }}</p>
          </div>
          <div class="summary-card">
            <div class="card-icon">
              <i class="fas fa-clock"></i>
            </div>
            <h3>Pending</h3>
            <p class="amount">R{{ pendingPayouts }}</p>
          </div>
          <div class="summary-card">
            <div class="card-icon">
              <i class="fas fa-check-circle"></i>
            </div>
            <h3>This Month</h3>
            <p class="amount">R{{ thisMonthPayouts }}</p>
          </div>
        </div>
        
        <div class="payouts-section">
          <h2>Recent Payouts</h2>
          <div class="payouts-grid">
            <div class="payout-item" *ngFor="let payout of payouts">
              <div class="payout-header">
                <div class="payout-info">
                  <i class="fas fa-receipt"></i>
                  <span class="payout-id">#{{ payout.id }}</span>
                </div>
                <span class="amount">R{{ payout.amount }}</span>
              </div>
              <div class="payout-meta">
                <div class="meta-item">
                  <i class="fas fa-calendar"></i>
                  <span class="date">{{ payout.date }}</span>
                </div>
                <div class="meta-item">
                  <i class="fas fa-credit-card"></i>
                  <span class="method">{{ payout.method }}</span>
                </div>
                <span class="status" [class]="payout.status">{{ payout.status }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Request Payout Modal -->
      <div class="modal-overlay" *ngIf="showRequestModal" (click)="closeRequestModal()">
        <div class="modal-content" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <h3>Request Payout</h3>
            <button class="close-btn" (click)="closeRequestModal()">×</button>
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
            <div class="form-group">
              <label>Reason</label>
              <textarea class="form-control" [(ngModel)]="form.reason" placeholder="Optional reason for payout"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" (click)="closeRequestModal()">Cancel</button>
            <button class="btn-primary" [disabled]="!form.stokvelId || !form.amount" (click)="submitRequest()">Submit Request</button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .payouts-page {
      position: relative;
      min-height: 100vh;
    }
    
    .payouts-container { 
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
    
    .payouts-section h2 { 
      color: #1a1a1a; 
      margin-bottom: 2rem; 
      font-size: 2rem;
      font-weight: 700;
      text-shadow: 0 1px 3px rgba(255, 255, 255, 0.8);
    }
    
    .payouts-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
      gap: 1.5rem;
    }
    
    .payout-item { 
      background: rgba(255, 255, 255, 0.95); 
      border: 1px solid rgba(255, 255, 255, 0.3); 
      border-radius: 1rem; 
      padding: 1.5rem; 
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      backdrop-filter: blur(20px);
      transition: all 0.3s ease;
    }
    
    .payout-item:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .payout-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }
    
    .payout-info {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    
    .payout-info i {
      color: var(--primary-color);
      font-size: 1.2rem;
    }
    
    .payout-id { 
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
    
    .payout-meta { 
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
    
    .status.rejected {
      background: rgba(220, 53, 69, 0.2);
      color: #dc3545;
      border: 1px solid rgba(220, 53, 69, 0.3);
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
    
    .btn-secondary { 
      background: rgba(255, 255, 255, 0.9); 
      color: #1a1a1a; 
      border: 1px solid rgba(0, 0, 0, 0.1); 
      padding: 0.75rem 1.5rem; 
      border-radius: 0.75rem; 
      cursor: pointer; 
      font-weight: 600;
      transition: all 0.3s ease;
    }
    
    .btn-secondary:hover {
      background: rgba(46, 139, 87, 0.1);
      border-color: var(--primary-color);
      transform: translateY(-1px);
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
      .payouts-container {
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
      
      .payouts-grid {
        grid-template-columns: 1fr;
      }
      
      .payout-meta {
        flex-direction: column;
        align-items: flex-start;
      }
    }
  `]
})
export class PayoutsPage {
  totalPayouts = 15000;
  pendingPayouts = 2500;
  thisMonthPayouts = 3500;
  
  stokvels: any[] = [];
  payouts: any[] = [];

  showRequestModal = false;
  form = { stokvelId: '', amount: 0, method: 'bank', reason: '' } as any;

  constructor(private api: ApiService) {
    this.stokvels = this.api.getStokvels();
    this.payouts = this.api.getPayouts();
  }

  openRequestModal() { this.showRequestModal = true; }
  closeRequestModal() { this.showRequestModal = false; this.form = { stokvelId: '', amount: 0, method: 'bank', reason: '' }; }
  
  submitRequest() {
    const payout = this.api.requestPayout(this.form);
    this.payouts = [...this.api.getPayouts()];
    this.closeRequestModal();
    alert('Payout request submitted');
  }
}
