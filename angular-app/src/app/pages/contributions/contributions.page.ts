import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-contributions',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="contributions-container">
      <div class="header">
        <h1>Contributions</h1>
        <button class="btn-primary" (click)="openModal()">Make New Contribution</button>
      </div>
      
      <div class="summary-cards">
        <div class="summary-card">
          <h3>Total Contributed</h3>
          <p class="amount">R{{ totalContributed }}</p>
        </div>
        <div class="summary-card">
          <h3>This Month</h3>
          <p class="amount">R{{ thisMonthContribution }}</p>
        </div>
        <div class="summary-card">
          <h3>Next Due</h3>
          <p class="date">{{ nextDueDate }}</p>
        </div>
      </div>
      
      <div class="contributions-list">
        <h2>Recent Contributions</h2>
        <div class="contribution-item" *ngFor="let contribution of contributions">
          <div class="contribution-info">
            <span class="stokvel-name">{{ contribution.stokvelName }}</span>
            <span class="amount">R{{ contribution.amount }}</span>
          </div>
          <div class="contribution-meta">
            <span class="date">{{ contribution.date }}</span>
            <span class="status" [class]="contribution.status">{{ contribution.status }}</span>
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
    .contributions-container { padding: 2rem; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
    .header h1 { color: #fff; }
    .btn-primary { background: var(--primary-color); color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; }
    .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
    .summary-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 1rem; padding: 1.5rem; text-align: center; }
    .summary-card h3 { color: rgba(255,255,255,0.7); font-size: 0.875rem; margin-bottom: 0.5rem; }
    .summary-card .amount { font-size: 2rem; font-weight: 700; color: var(--primary-color); }
    .summary-card .date { font-size: 1.25rem; font-weight: 600; color: #fff; }
    .contributions-list h2 { color: #fff; margin-bottom: 1rem; }
    .contribution-item { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 0.5rem; padding: 1rem; margin-bottom: 0.5rem; }
    .contribution-info { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
    .stokvel-name { color: #fff; font-weight: 600; }
    .amount { color: var(--primary-color); font-weight: 600; }
    .contribution-meta { display: flex; justify-content: space-between; }
    .date { color: rgba(255,255,255,0.6); font-size: 0.875rem; }
    .status { padding: 0.25rem 0.5rem; border-radius: 0.375rem; font-size: 0.75rem; }
    .status.completed { background: rgba(76,175,80,0.2); color: #4CAF50; }
    .modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.8);display:flex;align-items:center;justify-content:center;z-index:1000;backdrop-filter:blur(10px)}
    .modal-content{background:rgba(30,30,30,0.95);border:1px solid rgba(255,255,255,0.1);border-radius:1rem;width:90%;max-width:500px;overflow:hidden}
    .modal-header{display:flex;justify-content:space-between;align-items:center;padding:1rem 1.25rem;border-bottom:1px solid rgba(255,255,255,0.1)}
    .modal-body{padding:1rem 1.25rem}
    .modal-footer{display:flex;justify-content:flex-end;gap:.5rem;padding:1rem 1.25rem;border-top:1px solid rgba(255,255,255,0.1)}
    .close-btn{background:none;border:none;color:#aaa;font-size:1.25rem;cursor:pointer}
    .form-group{margin-bottom:1rem}
    .form-control{width:100%;padding:.6rem .75rem;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:.5rem;color:#fff}
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