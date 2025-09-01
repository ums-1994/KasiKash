import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="settings-container">
      <h1>Settings</h1>
      
      <div class="settings-section">
        <h3>Account Settings</h3>
        <div class="setting-item">
          <label>Email Notifications</label>
          <input type="checkbox" [(ngModel)]="settings.emailNotifications">
        </div>
        <div class="setting-item">
          <label>SMS Notifications</label>
          <input type="checkbox" [(ngModel)]="settings.smsNotifications">
        </div>
        <div class="setting-item">
          <label>Two-Factor Authentication</label>
          <input type="checkbox" [(ngModel)]="settings.twoFactorAuth">
        </div>
      </div>
      
      <div class="settings-section">
        <h3>Privacy Settings</h3>
        <div class="setting-item">
          <label>Profile Visibility</label>
          <select [(ngModel)]="settings.profileVisibility">
            <option value="public">Public</option>
            <option value="members">Members Only</option>
            <option value="private">Private</option>
          </select>
        </div>
        <div class="setting-item">
          <label>Show Contribution History</label>
          <input type="checkbox" [(ngModel)]="settings.showContributionHistory">
        </div>
      </div>
      
      <div class="settings-section">
        <h3>Language & Region</h3>
        <div class="setting-item">
          <label>Language</label>
          <select [(ngModel)]="settings.language">
            <option value="en">English</option>
            <option value="zu">Zulu</option>
            <option value="xh">Xhosa</option>
            <option value="af">Afrikaans</option>
          </select>
        </div>
        <div class="setting-item">
          <label>Currency</label>
          <select [(ngModel)]="settings.currency">
            <option value="ZAR">South African Rand (ZAR)</option>
            <option value="USD">US Dollar (USD)</option>
            <option value="EUR">Euro (EUR)</option>
          </select>
        </div>
      </div>
      
      <div class="settings-actions">
        <button class="btn-primary" (click)="save()">Save Changes</button>
        <button class="btn-secondary" (click)="reset()">Reset to Default</button>
      </div>
    </div>
  `,
  styles: [`
    .settings-container { padding: 2rem; max-width: 600px; margin: 0 auto; }
    h1 { color: #fff; margin-bottom: 2rem; }
    .settings-section { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 1rem; padding: 1.5rem; margin-bottom: 1.5rem; }
    .settings-section h3 { color: #fff; margin-bottom: 1rem; }
    .setting-item { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
    .setting-item label { color: rgba(255,255,255,0.8); font-weight: 500; }
    .setting-item input[type="checkbox"] { width: 18px; height: 18px; accent-color: #7B61FF; }
    .setting-item select { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #fff; padding: 0.5rem; border-radius: 0.375rem; }
    .settings-actions { display: flex; gap: 1rem; justify-content: center; }
    .btn-primary { background: var(--primary-color); color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; }
    .btn-secondary { background: rgba(255,255,255,0.1); color: #fff; border: 1px solid rgba(255,255,255,0.2); padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; }
  `]
})
export class SettingsPage {
  settings: any;

  constructor(private api: ApiService) {
    this.settings = this.api.getSettings();
  }

  save() {
    this.api.saveSettings(this.settings);
    alert('Settings saved');
  }

  reset() {
    this.settings = this.api.resetSettings();
  }
} 