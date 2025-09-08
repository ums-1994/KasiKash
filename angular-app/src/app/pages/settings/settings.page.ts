import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="settings-page">
      <div class="page-background"></div>
      <div class="page-overlay"></div>
      
    <div class="settings-container">
        <div class="header">
      <h1>Settings</h1>
          <p class="subtitle">Manage your account preferences and privacy settings</p>
        </div>
      
        <div class="settings-grid">
      <div class="settings-section">
            <div class="section-header">
              <i class="fas fa-user-cog"></i>
        <h3>Account Settings</h3>
            </div>
        <div class="setting-item">
              <div class="setting-info">
          <label>Email Notifications</label>
                <p>Receive updates about your stokvel activities</p>
              </div>
              <input type="checkbox" [(ngModel)]="settings.emailNotifications" class="toggle">
        </div>
        <div class="setting-item">
              <div class="setting-info">
          <label>SMS Notifications</label>
                <p>Get text messages for important updates</p>
              </div>
              <input type="checkbox" [(ngModel)]="settings.smsNotifications" class="toggle">
        </div>
        <div class="setting-item">
              <div class="setting-info">
          <label>Two-Factor Authentication</label>
                <p>Add an extra layer of security to your account</p>
              </div>
              <input type="checkbox" [(ngModel)]="settings.twoFactorAuth" class="toggle">
        </div>
      </div>
      
      <div class="settings-section">
            <div class="section-header">
              <i class="fas fa-shield-alt"></i>
        <h3>Privacy Settings</h3>
            </div>
        <div class="setting-item">
              <div class="setting-info">
          <label>Profile Visibility</label>
                <p>Control who can see your profile information</p>
              </div>
              <select [(ngModel)]="settings.profileVisibility" class="form-control">
            <option value="public">Public</option>
            <option value="members">Members Only</option>
            <option value="private">Private</option>
          </select>
        </div>
        <div class="setting-item">
              <div class="setting-info">
          <label>Show Contribution History</label>
                <p>Allow other members to see your contribution history</p>
              </div>
              <input type="checkbox" [(ngModel)]="settings.showContributionHistory" class="toggle">
        </div>
      </div>
      
      <div class="settings-section">
            <div class="section-header">
              <i class="fas fa-globe"></i>
        <h3>Language & Region</h3>
            </div>
        <div class="setting-item">
              <div class="setting-info">
          <label>Language</label>
                <p>Choose your preferred language</p>
              </div>
              <select [(ngModel)]="settings.language" class="form-control">
            <option value="en">English</option>
            <option value="zu">Zulu</option>
            <option value="xh">Xhosa</option>
            <option value="af">Afrikaans</option>
          </select>
        </div>
        <div class="setting-item">
              <div class="setting-info">
          <label>Currency</label>
                <p>Select your preferred currency for display</p>
              </div>
              <select [(ngModel)]="settings.currency" class="form-control">
            <option value="ZAR">South African Rand (ZAR)</option>
            <option value="USD">US Dollar (USD)</option>
            <option value="EUR">Euro (EUR)</option>
          </select>
            </div>
        </div>
      </div>
      
      <div class="settings-actions">
          <button class="btn-secondary" (click)="reset()">
            <i class="fas fa-undo"></i> Reset to Default
          </button>
          <button class="btn-primary" (click)="save()">
            <i class="fas fa-save"></i> Save Changes
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .settings-page {
      position: relative;
      min-height: 100vh;
    }
    
    .settings-container { 
      padding: 2rem; 
      max-width: 1200px; 
      margin: 0 auto; 
      position: relative;
      z-index: 1;
    }
    
    .header {
      text-align: center;
      margin-bottom: 3rem;
    }
    
    .header h1 { 
      color: #1a1a1a;
      text-shadow: 0 1px 3px rgba(255, 255, 255, 0.8);
      font-size: 2.5rem;
      font-weight: 800;
      margin-bottom: 0.5rem;
    }
    
    .subtitle {
      color: #2b2b2b;
      font-size: 1.1rem;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .settings-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
      gap: 2rem;
      margin-bottom: 3rem;
    }
    
    .settings-section { 
      background: rgba(255, 255, 255, 0.95); 
      border: 1px solid rgba(255, 255, 255, 0.3); 
      border-radius: 1.5rem; 
      padding: 2rem; 
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      backdrop-filter: blur(20px);
      transition: all 0.3s ease;
    }
    
    .settings-section:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .section-header {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 2rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid rgba(0, 0, 0, 0.1);
    }
    
    .section-header i {
      color: var(--primary-color);
      font-size: 1.5rem;
    }
    
    .section-header h3 { 
      color: #1a1a1a; 
      margin: 0;
      font-size: 1.5rem;
      font-weight: 700;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .setting-item { 
      display: flex; 
      justify-content: space-between; 
      align-items: center; 
      margin-bottom: 2rem;
      padding: 1rem;
      background: rgba(255, 255, 255, 0.5);
      border-radius: 1rem;
      transition: all 0.3s ease;
    }
    
    .setting-item:hover {
      background: rgba(255, 255, 255, 0.7);
    }
    
    .setting-info {
      flex: 1;
    }
    
    .setting-info label { 
      color: #1a1a1a; 
      font-weight: 600; 
      font-size: 1.1rem;
      display: block;
      margin-bottom: 0.25rem;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .setting-info p {
      color: #2b2b2b;
      font-size: 0.9rem;
      margin: 0;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .toggle {
      width: 50px;
      height: 25px;
      background: #ccc;
      border-radius: 25px;
      position: relative;
      cursor: pointer;
      transition: all 0.3s ease;
      border: none;
      outline: none;
    }
    
    .toggle:checked {
      background: var(--primary-color);
    }
    
    .toggle::before {
      content: '';
      position: absolute;
      width: 21px;
      height: 21px;
      background: white;
      border-radius: 50%;
      top: 2px;
      left: 2px;
      transition: all 0.3s ease;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .toggle:checked::before {
      transform: translateX(25px);
    }
    
    .form-control {
      background: rgba(255, 255, 255, 0.9);
      border: 1px solid rgba(0, 0, 0, 0.1);
      color: #1a1a1a;
      padding: 0.75rem 1rem;
      border-radius: 0.75rem;
      font-size: 1rem;
      transition: all 0.3s ease;
      min-width: 200px;
    }
    
    .form-control:focus {
      outline: none;
      border-color: var(--primary-color);
      box-shadow: 0 0 0 3px rgba(46, 139, 87, 0.1);
    }
    
    .settings-actions { 
      display: flex; 
      gap: 1.5rem; 
      justify-content: center;
      flex-wrap: wrap;
    }
    
    .btn-primary { 
      background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); 
      color: white; 
      border: none; 
      padding: 0.75rem 2rem; 
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
    
    .btn-secondary { 
      background: rgba(255, 255, 255, 0.9); 
      color: #1a1a1a; 
      border: 1px solid rgba(0, 0, 0, 0.1); 
      padding: 0.75rem 2rem; 
      border-radius: 0.75rem; 
      cursor: pointer; 
      font-weight: 600;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    
    .btn-secondary:hover {
      background: rgba(46, 139, 87, 0.1);
      border-color: var(--primary-color);
      transform: translateY(-1px);
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
      .settings-container {
        padding: 1rem;
      }
      
      .header h1 {
        font-size: 2rem;
      }
      
      .settings-grid {
        grid-template-columns: 1fr;
        gap: 1.5rem;
      }
      
      .setting-item {
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
      }
      
      .form-control {
        min-width: 100%;
      }
      
      .settings-actions {
        flex-direction: column;
        align-items: center;
      }
      
      .btn-primary,
      .btn-secondary {
        width: 100%;
        justify-content: center;
      }
    }
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