import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-stokvels',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="stokvels-container">
      <div class="header">
        <h1>My Stokvels</h1>
        <button class="btn-primary" (click)="openCreate()">Create New Stokvel</button>
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
            <p><strong>Members:</strong> {{ stokvel.memberCount }}</p>
            <p><strong>Monthly Contribution:</strong> R{{ stokvel.monthlyContribution }}</p>
            <p><strong>Total Fund:</strong> R{{ stokvel.totalFund }}</p>
          </div>
          <div class="stokvel-actions">
            <button class="btn-secondary" (click)="viewDetails(stokvel)">View Details</button>
            <button class="btn-secondary" (click)="makeContribution(stokvel)">Make Contribution</button>
            <button class="btn-secondary" (click)="viewMembers(stokvel)">View Members</button>
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
    .stokvels-container { padding: 2rem; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
    .header h1 { color: #003B70; }
    .btn-primary { background: var(--primary-color); color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; }
    .stokvels-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
    .stokvel-card { background: #ffffff; border: 1px solid rgba(0,59,112,0.15); border-radius: 1rem; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,59,112,0.06); }
    .stokvel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
    .stokvel-header h3 { color: #003B70; }
    .stokvel-badges { display: flex; gap: 0.5rem; }
    .status { padding: 0.25rem 0.75rem; border-radius: 0.375rem; font-size: 0.75rem; font-weight: 600; }
    .status.active { background: rgba(46,125,50,0.15); color: var(--success-color); }
    .role-badge { padding: 0.25rem 0.75rem; border-radius: 0.375rem; font-size: 0.75rem; font-weight: 600; text-transform: capitalize; }
    .role-badge.admin { background: rgba(220,53,69,0.15); color: #dc3545; }
    .role-badge.member { background: rgba(0,123,255,0.15); color: #007bff; }
    .stokvel-details p { color: #1a4a7a; margin-bottom: 0.5rem; }
    .stokvel-actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
    .btn-secondary { background: #ffffff; color: #003B70; border: 1px solid rgba(0,59,112,0.15); padding: 0.5rem 1rem; border-radius: 0.375rem; cursor: pointer; }
    .btn-danger { background: rgba(220,53,69,0.2); color: #dc3545; border: 1px solid rgba(220,53,69,0.3); padding: 0.5rem 1rem; border-radius: 0.375rem; cursor: pointer; transition: all 0.3s ease; }
    .btn-danger:hover { background: rgba(220,53,69,0.3); border-color: #dc3545; }
    .btn-warning { background: rgba(255,193,7,0.2); color: #ffc107; border: 1px solid rgba(255,193,7,0.3); padding: 0.5rem 1rem; border-radius: 0.375rem; cursor: pointer; transition: all 0.3s ease; }
    .btn-warning:hover { background: rgba(255,193,7,0.3); border-color: #ffc107; }
    .delete-modal { max-width: 600px; }
    .delete-warning { text-align: center; color: #003B70; }
    .delete-warning i { font-size: 3rem; color: #ffc107; margin-bottom: 1rem; }
    .delete-warning ul { text-align: left; margin: 1rem 0; padding-left: 2rem; }
    .delete-warning li { margin-bottom: 0.5rem; color: #1a4a7a; }
    /* Reuse modal & form styles similar to dashboard */
    .modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;z-index:1000;backdrop-filter:blur(10px)}
    .modal-content{background:#ffffff;border:1px solid rgba(0,59,112,0.15);border-radius:1rem;width:90%;max-width:500px;overflow:hidden;box-shadow:0 10px 30px rgba(0,59,112,0.15)}
    .modal-header{display:flex;justify-content:space-between;align-items:center;padding:1rem 1.25rem;border-bottom:1px solid rgba(0,59,112,0.1)}
    .modal-body{padding:1rem 1.25rem}
    .modal-footer{display:flex;justify-content:flex-end;gap:.5rem;padding:1rem 1.25rem;border-top:1px solid rgba(0,59,112,0.1)}
    .close-btn{background:none;border:none;color:#5a7a9a;font-size:1.25rem;cursor:pointer}
    .form-group{margin-bottom:1rem}
    .form-control{width:100%;padding:.6rem .75rem;background:#ffffff;border:1px solid rgba(0,59,112,0.15);border-radius:.5rem;color:#003B70}
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