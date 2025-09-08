import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-stokvels',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="stokvels-page">
      <div class="page-background"></div>
      <div class="page-overlay"></div>
      
    <div class="stokvels-container">
      <div class="header">
        <h1>My Stokvels</h1>
          <button class="btn-primary" (click)="openCreate()">
            <i class="fas fa-plus"></i> Create New Stokvel
          </button>
      </div>
      
      <div class="stokvels-grid">
        <div class="stokvel-card" *ngFor="let stokvel of stokvels">
          <div class="stokvel-header">
            <h3>{{ stokvel.name }}</h3>
            <div class="stokvel-badges">
              <span class="status" [class]="stokvel.status">{{ stokvel.status }}</span>
              <span class="role-badge" [class]="stokvel.role">{{ stokvel.role }}</span>
            </div>
          </div>
          <div class="stokvel-details">
              <div class="detail-item">
                <i class="fas fa-users"></i>
                <span><strong>Members:</strong> {{ stokvel.memberCount }}</span>
              </div>
              <div class="detail-item">
                <i class="fas fa-dollar-sign"></i>
                <span><strong>Monthly Contribution:</strong> R{{ stokvel.monthlyContribution }}</span>
              </div>
              <div class="detail-item">
                <i class="fas fa-piggy-bank"></i>
                <span><strong>Total Fund:</strong> R{{ stokvel.totalFund }}</span>
              </div>
          </div>
          <div class="stokvel-actions">
              <button class="btn-secondary" (click)="viewDetails(stokvel)">
                <i class="fas fa-eye"></i> View Details
              </button>
              <button class="btn-secondary" (click)="makeContribution(stokvel)">
                <i class="fas fa-plus-circle"></i> Make Contribution
              </button>
              <button class="btn-secondary" (click)="viewMembers(stokvel)">
                <i class="fas fa-users"></i> View Members
              </button>
            <button *ngIf="stokvel.role === 'admin' || stokvel.isCreator" 
                    class="btn-danger" 
                    (click)="confirmDelete(stokvel)" 
                    title="Delete Stokvel">
              <i class="fas fa-trash"></i> Delete
            </button>
            <button *ngIf="stokvel.role !== 'admin' && !stokvel.isCreator" 
                    class="btn-warning" 
                    (click)="leaveStokvel(stokvel)" 
                    title="Leave Stokvel">
              <i class="fas fa-sign-out-alt"></i> Leave
            </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Create Stokvel Modal -->
      <div class="modal-overlay" *ngIf="showCreate" (click)="closeCreate()">
        <div class="modal-content" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <h3>Create New Stokvel</h3>
            <button class="close-btn" (click)="closeCreate()">×</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>Name</label>
              <input class="form-control" [(ngModel)]="form.name" placeholder="Stokvel name" />
            </div>
            <div class="form-group">
              <label>Monthly Contribution (R)</label>
              <input type="number" class="form-control" [(ngModel)]="form.contributionAmount" />
            </div>
            <div class="form-group">
              <label>Meeting Day</label>
              <select class="form-control" [(ngModel)]="form.meetingDay">
                <option value="monday">Monday</option>
                <option value="tuesday">Tuesday</option>
                <option value="wednesday">Wednesday</option>
                <option value="thursday">Thursday</option>
                <option value="friday">Friday</option>
                <option value="saturday">Saturday</option>
                <option value="sunday">Sunday</option>
              </select>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" (click)="closeCreate()">Cancel</button>
            <button class="btn-primary" [disabled]="!form.name || !form.contributionAmount" (click)="submitCreate()">Create</button>
          </div>
        </div>
      </div>

      <!-- Delete Confirmation Modal -->
      <div class="modal-overlay" *ngIf="showDeleteConfirm" (click)="cancelDelete()">
        <div class="modal-content delete-modal" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <h3>Delete Stokvel</h3>
            <button class="close-btn" (click)="cancelDelete()">×</button>
          </div>
          <div class="modal-body">
            <div class="delete-warning">
              <i class="fas fa-exclamation-triangle"></i>
              <p><strong>Are you sure you want to delete "{{ stokvelToDelete?.name }}"?</strong></p>
              <p>This action cannot be undone. All stokvel data including:</p>
              <ul>
                <li>Member information</li>
                <li>Contribution history</li>
                <li>Financial records</li>
                <li>Meeting schedules</li>
              </ul>
              <p>will be permanently deleted.</p>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" (click)="cancelDelete()">Cancel</button>
            <button class="btn-danger" (click)="deleteStokvel()">
              <i class="fas fa-trash"></i> Delete Permanently
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .stokvels-page {
      position: relative;
      min-height: 100vh;
    }
    
    .stokvels-container { 
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
    
    .stokvels-grid { 
      display: grid; 
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); 
      gap: 2rem; 
    }
    
    .stokvel-card { 
      background: rgba(255, 255, 255, 0.95); 
      border: 1px solid rgba(255, 255, 255, 0.3); 
      border-radius: 1.5rem; 
      padding: 2rem; 
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      backdrop-filter: blur(20px);
      transition: all 0.3s ease;
    }
    
    .stokvel-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .stokvel-header { 
      display: flex; 
      justify-content: space-between; 
      align-items: flex-start; 
      margin-bottom: 1.5rem; 
      flex-wrap: wrap;
      gap: 1rem;
    }
    
    .stokvel-header h3 { 
      color: #1a1a1a; 
      font-size: 1.5rem;
      font-weight: 700;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .stokvel-badges { 
      display: flex; 
      gap: 0.5rem; 
      flex-wrap: wrap;
    }
    
    .status { 
      padding: 0.375rem 0.75rem; 
      border-radius: 0.5rem; 
      font-size: 0.75rem; 
      font-weight: 600; 
      text-transform: uppercase;
    }
    
    .status.active { 
      background: rgba(46, 139, 87, 0.2); 
      color: var(--success-color); 
      border: 1px solid rgba(46, 139, 87, 0.3);
    }
    
    .role-badge { 
      padding: 0.375rem 0.75rem; 
      border-radius: 0.5rem; 
      font-size: 0.75rem; 
      font-weight: 600; 
      text-transform: capitalize; 
    }
    
    .role-badge.admin { 
      background: rgba(220, 53, 69, 0.2); 
      color: #dc3545; 
      border: 1px solid rgba(220, 53, 69, 0.3);
    }
    
    .role-badge.member { 
      background: rgba(0, 123, 255, 0.2); 
      color: #007bff; 
      border: 1px solid rgba(0, 123, 255, 0.3);
    }
    
    .stokvel-details {
      margin-bottom: 1.5rem;
    }
    
    .detail-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 0.75rem;
      color: #2b2b2b;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .detail-item i {
      color: var(--primary-color);
      width: 16px;
      text-align: center;
    }
    
    .stokvel-actions { 
      display: flex; 
      gap: 0.75rem; 
      margin-top: 1.5rem; 
      flex-wrap: wrap;
    }
    
    .btn-secondary { 
      background: rgba(255, 255, 255, 0.9); 
      color: #1a1a1a; 
      border: 1px solid rgba(0, 0, 0, 0.1); 
      padding: 0.5rem 1rem; 
      border-radius: 0.5rem; 
      cursor: pointer; 
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: 500;
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
      padding: 0.5rem 1rem; 
      border-radius: 0.5rem; 
      cursor: pointer; 
      transition: all 0.3s ease; 
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    
    .btn-danger:hover { 
      background: rgba(220, 53, 69, 0.3); 
      border-color: #dc3545; 
      transform: translateY(-1px);
    }
    
    .btn-warning { 
      background: rgba(255, 193, 7, 0.2); 
      color: #ffc107; 
      border: 1px solid rgba(255, 193, 7, 0.3); 
      padding: 0.5rem 1rem; 
      border-radius: 0.5rem; 
      cursor: pointer; 
      transition: all 0.3s ease; 
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    
    .btn-warning:hover { 
      background: rgba(255, 193, 7, 0.3); 
      border-color: #ffc107; 
      transform: translateY(-1px);
    }
    
    .delete-modal { max-width: 600px; }
    .delete-warning { text-align: center; color: #1a1a1a; }
    .delete-warning i { font-size: 3rem; color: #ffc107; margin-bottom: 1rem; }
    .delete-warning ul { text-align: left; margin: 1rem 0; padding-left: 2rem; }
    .delete-warning li { margin-bottom: 0.5rem; color: #2b2b2b; }
    
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
      .stokvels-container {
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
      
      .stokvels-grid {
        grid-template-columns: 1fr;
        gap: 1.5rem;
      }
      
      .stokvel-actions {
        flex-direction: column;
      }
      
      .stokvel-actions button {
        width: 100%;
        justify-content: center;
      }
    }
  `]
})
export class StokvelsPage {
  stokvels: any[] = [];
  showCreate = false;
  showDeleteConfirm = false;
  stokvelToDelete: any = null;
  form = { name: '', contributionAmount: 0, meetingDay: 'monday' } as any;

  constructor(private api: ApiService) {
    this.stokvels = this.api.getStokvels();
  }

  openCreate() { this.showCreate = true; }
  closeCreate() { this.showCreate = false; this.form = { name: '', contributionAmount: 0, meetingDay: 'monday' }; }
  
  submitCreate() {
    const created = this.api.createStokvel(this.form);
    this.stokvels = [...this.api.getStokvels()];
    this.closeCreate();
    alert(`Created ${created.name}`);
  }

  viewDetails(stokvel: any) {
    alert(`${stokvel.name} details coming soon`);
  }

  makeContribution(stokvel: any) {
    alert(`Navigate to contributions with ${stokvel.name}`);
  }

  viewMembers(stokvel: any) {
    alert(`View members for ${stokvel.name} - coming soon`);
  }

  leaveStokvel(stokvel: any) {
    const confirmLeave = confirm(`Are you sure you want to leave "${stokvel.name}" stokvel? You will lose access to all stokvel information and contributions.`);
    if (confirmLeave) {
      const result = this.api.leaveStokvel(stokvel.id);
      if (result.success) {
        this.stokvels = [...this.api.getStokvels()];
        alert(result.message);
      } else {
        alert(`Error: ${result.message}`);
      }
    }
  }

  confirmDelete(stokvel: any) {
    this.stokvelToDelete = stokvel;
    this.showDeleteConfirm = true;
  }

  cancelDelete() {
    this.showDeleteConfirm = false;
    this.stokvelToDelete = null;
  }

  deleteStokvel() {
    if (!this.stokvelToDelete) return;
    
    // Additional safety check - warn if stokvel has funds
    if (this.stokvelToDelete.totalFund > 0) {
      const proceed = confirm(`Warning: This stokvel has R${this.stokvelToDelete.totalFund} in funds. Are you sure you want to delete it? All funds will be lost.`);
      if (!proceed) return;
    }
    
    const result = this.api.deleteStokvel(this.stokvelToDelete.id);
    
    if (result.success) {
      this.stokvels = [...this.api.getStokvels()];
      this.cancelDelete();
      alert(result.message);
    } else {
      alert(`Error: ${result.message}`);
    }
  }
} 