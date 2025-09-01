import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="profile-container">
      <div class="profile-header">
        <div class="profile-avatar">
          <img src="assets/default-avatar.png" alt="Profile" class="avatar-img">
          <button class="edit-avatar">Edit</button>
        </div>
        <div class="profile-info">
          <h1>{{ userProfile.name }}</h1>
          <p class="email">{{ userProfile.email }}</p>
          <p class="member-since">Member since {{ userProfile.memberSince }}</p>
        </div>
      </div>
      
      <div class="profile-details">
        <div class="detail-section">
          <h3>Personal Information</h3>
          <div class="detail-item">
            <label>Full Name:</label>
            <span>{{ userProfile.name }}</span>
          </div>
          <div class="detail-item">
            <label>Phone:</label>
            <span>{{ userProfile.phone }}</span>
          </div>
          <div class="detail-item">
            <label>Address:</label>
            <span>{{ userProfile.address }}</span>
          </div>
        </div>
        
        <div class="detail-section">
          <h3>KYC Status</h3>
          <div class="kyc-status" [class]="userProfile.kycStatus">
            <span class="status-badge">{{ userProfile.kycStatus }}</span>
            <p>{{ userProfile.kycStatus === 'verified' ? 'Your identity has been verified' : 'Please complete KYC verification' }}</p>
          </div>
        </div>
      </div>
      
      <div class="profile-actions">
        <button class="btn-primary" (click)="editProfile()">Edit Profile</button>
        <button class="btn-secondary">Change Password</button>
        <button class="btn-secondary" (click)="downloadStatement()">Download Statement</button>
      </div>
    </div>
  `,
  styles: [`
    .profile-container { padding: 2rem; max-width: 800px; margin: 0 auto; }
    .profile-header { display: flex; gap: 2rem; margin-bottom: 2rem; }
    .profile-avatar { text-align: center; }
    .avatar-img { width: 120px; height: 120px; border-radius: 50%; border: 4px solid var(--primary-color); }
    .edit-avatar { background: var(--primary-color); color: white; border: none; padding: 0.5rem 1rem; border-radius: 0.5rem; margin-top: 1rem; cursor: pointer; }
    .profile-info h1 { color: #fff; font-size: 2rem; margin-bottom: 0.5rem; }
    .email { color: rgba(255,255,255,0.7); margin-bottom: 0.5rem; }
    .member-since { color: rgba(255,255,255,0.6); }
    .detail-section { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 1rem; padding: 1.5rem; margin-bottom: 1.5rem; }
    .detail-section h3 { color: #fff; margin-bottom: 1rem; }
    .detail-item { display: flex; justify-content: space-between; margin-bottom: 0.75rem; }
    .detail-item label { color: rgba(255,255,255,0.7); font-weight: 600; }
    .detail-item span { color: #fff; }
    .kyc-status { text-align: center; }
    .status-badge { background: rgba(46,125,50,0.15); color: var(--success-color); padding: 0.5rem 1rem; border-radius: 0.5rem; font-weight: 600; }
    .kyc-status p { color: rgba(255,255,255,0.8); margin-top: 1rem; }
    .profile-actions { display: flex; gap: 1rem; justify-content: center; }
    .btn-primary { background: var(--primary-color); color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; }
    .btn-secondary { background: rgba(255,255,255,0.1); color: #fff; border: 1px solid rgba(255,255,255,0.2); padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; }
  `]
})
export class ProfilePage {
  userProfile = {
    name: 'John Doe',
    email: 'john.doe@example.com',
    phone: '+27 123 456 789',
    address: '123 Main Street, Johannesburg, South Africa',
    memberSince: 'January 2024',
    kycStatus: 'verified'
  };

  constructor(private api: ApiService) {
    const current = this.api.getCurrentUser();
    this.userProfile.name = current.name;
    this.userProfile.email = current.email;
  }

  editProfile() {
    const name = prompt('Update name', this.userProfile.name);
    if (name) {
      this.userProfile.name = name;
      const current = this.api.getCurrentUser();
      this.api.setCurrentUser({ ...current, name });
      alert('Profile updated');
    }
  }

  downloadStatement() {
    const blob = new Blob([`Statement for ${this.userProfile.name} on ${new Date().toISOString()}`], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'statement.txt';
    a.click();
    URL.revokeObjectURL(url);
  }
} 