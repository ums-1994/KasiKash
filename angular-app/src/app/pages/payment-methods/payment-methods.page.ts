import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-payment-methods',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="payment-methods-page">
      <div class="page-background"></div>
      <div class="page-overlay"></div>
      
      <div class="payment-methods-container">
        <div class="header">
          <h1>Payment Methods</h1>
          <button class="btn-primary" (click)="openAddModal()">
            <i class="fas fa-plus"></i> Add Payment Method
          </button>
        </div>
        
        <div class="payment-methods-grid">
          <div class="payment-method-card" *ngFor="let method of paymentMethods">
            <div class="method-header">
              <div class="method-icon">
                <i [class]="getMethodIcon(method.type)"></i>
              </div>
              <div class="method-info">
                <h3>{{ method.name }}</h3>
                <p class="method-details">{{ method.details }}</p>
              </div>
              <div class="method-actions">
                <button class="btn-secondary" (click)="editMethod(method)">
                  <i class="fas fa-edit"></i>
                </button>
                <button class="btn-danger" (click)="deleteMethod(method)">
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </div>
            <div class="method-meta">
              <span class="status" [class]="method.isDefault ? 'default' : 'secondary'">
                {{ method.isDefault ? 'Default' : 'Secondary' }}
              </span>
              <span class="added-date">Added {{ method.addedDate }}</span>
            </div>
          </div>
        </div>
        
        <div class="empty-state" *ngIf="paymentMethods.length === 0">
          <i class="fas fa-credit-card"></i>
          <h3>No Payment Methods</h3>
          <p>Add a payment method to start making contributions and receiving payouts.</p>
          <button class="btn-primary" (click)="openAddModal()">
            <i class="fas fa-plus"></i> Add Your First Payment Method
          </button>
        </div>
      </div>

      <!-- Add/Edit Payment Method Modal -->
      <div class="modal-overlay" *ngIf="showModal" (click)="closeModal()">
        <div class="modal-content" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <h3>{{ editingMethod ? 'Edit Payment Method' : 'Add Payment Method' }}</h3>
            <button class="close-btn" (click)="closeModal()">×</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>Payment Type</label>
              <select class="form-control" [(ngModel)]="form.type">
                <option value="bank">Bank Account</option>
                <option value="card">Credit/Debit Card</option>
                <option value="mobile">Mobile Money</option>
                <option value="ewallet">E-Wallet</option>
              </select>
            </div>
            <div class="form-group">
              <label>Account/Card Name</label>
              <input type="text" class="form-control" [(ngModel)]="form.name" placeholder="e.g., My FNB Account" />
            </div>
            <div class="form-group">
              <label>Account/Card Details</label>
              <input type="text" class="form-control" [(ngModel)]="form.details" placeholder="e.g., ****1234" />
            </div>
            <div class="form-group">
              <label>Bank/Provider</label>
              <input type="text" class="form-control" [(ngModel)]="form.provider" placeholder="e.g., First National Bank" />
            </div>
            <div class="form-group">
              <label>
                <input type="checkbox" [(ngModel)]="form.isDefault" class="checkbox" />
                Set as default payment method
              </label>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" (click)="closeModal()">Cancel</button>
            <button class="btn-primary" [disabled]="!form.name || !form.details" (click)="saveMethod()">
              {{ editingMethod ? 'Update' : 'Add' }} Payment Method
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .payment-methods-page {
      position: relative;
      min-height: 100vh;
    }
    
    .payment-methods-container { 
      padding: 2rem; 
      position: relative;
      z-index: 1;
    }
    
    .header { 
      display: flex; 
      justify-content: space-between; 
      align-items: center; 
      margin-bottom: 3rem; 
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
    
    .payment-methods-grid { 
      display: grid; 
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); 
      gap: 2rem; 
    }
    
    .payment-method-card { 
      background: rgba(255, 255, 255, 0.95); 
      border: 1px solid rgba(255, 255, 255, 0.3); 
      border-radius: 1.5rem; 
      padding: 2rem; 
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      backdrop-filter: blur(20px);
      transition: all 0.3s ease;
    }
    
    .payment-method-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .method-header {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1.5rem;
    }
    
    .method-icon {
      width: 60px;
      height: 60px;
      background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 1.5rem;
    }
    
    .method-info {
      flex: 1;
    }
    
    .method-info h3 { 
      color: #1a1a1a; 
      margin-bottom: 0.5rem; 
      font-size: 1.3rem;
      font-weight: 700;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .method-details { 
      color: #2b2b2b; 
      font-size: 1rem;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .method-actions {
      display: flex;
      gap: 0.5rem;
    }
    
    .btn-secondary { 
      background: rgba(255, 255, 255, 0.9); 
      color: #1a1a1a; 
      border: 1px solid rgba(0, 0, 0, 0.1); 
      padding: 0.5rem; 
      border-radius: 0.5rem; 
      cursor: pointer; 
      transition: all 0.3s ease;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .btn-secondary:hover {
      background: rgba(46, 139, 87, 0.1);
      border-color: var(--primary-color);
      transform: translateY(-1px);
    }
    
    .btn-danger { 
      background: rgba(220, 53, 69, 0.2); 
      color: #dc3545; 
      border: 1px solid rgba(220, 53, 69, 0.3); 
      padding: 0.5rem; 
      border-radius: 0.5rem; 
      cursor: pointer; 
      transition: all 0.3s ease;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .btn-danger:hover { 
      background: rgba(220, 53, 69, 0.3); 
      border-color: #dc3545; 
      transform: translateY(-1px);
    }
    
    .method-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }
    
    .status { 
      padding: 0.375rem 0.75rem; 
      border-radius: 0.5rem; 
      font-size: 0.75rem; 
      font-weight: 600;
      text-transform: uppercase;
    }
    
    .status.default { 
      background: rgba(46, 139, 87, 0.2); 
      color: var(--success-color); 
      border: 1px solid rgba(46, 139, 87, 0.3);
    }
    
    .status.secondary {
      background: rgba(0, 0, 0, 0.1);
      color: #2b2b2b;
      border: 1px solid rgba(0, 0, 0, 0.1);
    }
    
    .added-date {
      color: #2b2b2b;
      font-size: 0.9rem;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .empty-state {
      text-align: center;
      padding: 4rem 2rem;
      background: rgba(255, 255, 255, 0.95);
      border: 1px solid rgba(255, 255, 255, 0.3);
      border-radius: 1.5rem;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      backdrop-filter: blur(20px);
    }
    
    .empty-state i {
      font-size: 4rem;
      color: var(--primary-color);
      margin-bottom: 1.5rem;
    }
    
    .empty-state h3 {
      color: #1a1a1a;
      font-size: 1.5rem;
      font-weight: 700;
      margin-bottom: 1rem;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .empty-state p {
      color: #2b2b2b;
      font-size: 1.1rem;
      margin-bottom: 2rem;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
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
    
    .checkbox {
      width: 18px;
      height: 18px;
      accent-color: var(--primary-color);
      margin-right: 0.5rem;
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
      .payment-methods-container {
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
      
      .payment-methods-grid {
        grid-template-columns: 1fr;
        gap: 1.5rem;
      }
      
      .method-header {
        flex-direction: column;
        text-align: center;
      }
      
      .method-actions {
        justify-content: center;
      }
      
      .method-meta {
        flex-direction: column;
        text-align: center;
      }
    }
  `]
})
export class PaymentMethodsPage {
  paymentMethods: any[] = [];
  showModal = false;
  editingMethod: any = null;
  form = { type: 'bank', name: '', details: '', provider: '', isDefault: false } as any;

  constructor(private api: ApiService) {
    this.paymentMethods = this.api.getPaymentMethods();
  }

  getMethodIcon(type: string): string {
    const icons: { [key: string]: string } = {
      'bank': 'fas fa-university',
      'card': 'fas fa-credit-card',
      'mobile': 'fas fa-mobile-alt',
      'ewallet': 'fas fa-wallet'
    };
    return icons[type] || 'fas fa-credit-card';
  }

  openAddModal() { 
    this.editingMethod = null;
    this.form = { type: 'bank', name: '', details: '', provider: '', isDefault: false };
    this.showModal = true; 
  }
  
  editMethod(method: any) {
    this.editingMethod = method;
    this.form = { ...method };
    this.showModal = true;
  }
  
  closeModal() { 
    this.showModal = false; 
    this.editingMethod = null;
    this.form = { type: 'bank', name: '', details: '', provider: '', isDefault: false };
  }
  
  saveMethod() {
    if (this.editingMethod) {
      this.api.updatePaymentMethod(this.editingMethod.id, this.form);
    } else {
      this.api.addPaymentMethod(this.form);
    }
    this.paymentMethods = [...this.api.getPaymentMethods()];
    this.closeModal();
    alert(`Payment method ${this.editingMethod ? 'updated' : 'added'} successfully`);
  }
  
  deleteMethod(method: any) {
    if (confirm(`Are you sure you want to delete "${method.name}"?`)) {
      this.api.deletePaymentMethod(method.id);
      this.paymentMethods = [...this.api.getPaymentMethods()];
      alert('Payment method deleted');
    }
  }
}
