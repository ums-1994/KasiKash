import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-navigation',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <!-- Sidebar -->
    <div class="main-nav">
      <!-- Logo -->
      <div class="nav-header">
        <div class="logo">
          <h2>KasiKash</h2>
        </div>
        <div class="user-info">
          <div class="user-avatar">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-base">
              {{ getUserInitials() }}
            </div>
          </div>
          <div class="username">{{ currentUser?.name || 'User' }}</div>
        </div>
      </div>
      
      <!-- Navigation -->
      <ul class="nav-menu">
        <li>
          <a routerLink="/dashboard" routerLinkActive="active" class="nav-link">
            <i class="fas fa-home"></i> Home
          </a>
        </li>
        <li>
          <a routerLink="/stokvels" routerLinkActive="active" class="nav-link">
            <i class="fas fa-users"></i> Stokvels
          </a>
        </li>
        <li>
          <a routerLink="/contributions" routerLinkActive="active" class="nav-link">
            <i class="fas fa-dollar-sign"></i> Contributions
          </a>
        </li>
        <li>
          <a routerLink="/payouts" routerLinkActive="active" class="nav-link">
            <i class="fas fa-wallet"></i> Payouts
          </a>
        </li>
        <li>
          <a routerLink="/savings-goals" routerLinkActive="active" class="nav-link">
            <i class="fas fa-chart-line"></i> Savings Goals
          </a>
        </li>
        <li>
          <a routerLink="/payment-methods" routerLinkActive="active" class="nav-link">
            <i class="fas fa-credit-card"></i> Payment Methods
          </a>
        </li>
        <li>
          <a routerLink="/rewards" routerLinkActive="active" class="nav-link">
            <i class="fas fa-gift"></i> My Rewards Card
          </a>
        </li>
        <li>
          <a routerLink="/settings" routerLinkActive="active" class="nav-link">
            <i class="fas fa-cog"></i> Settings
          </a>
        </li>
        <li *ngIf="isAdmin">
          <a routerLink="/admin" routerLinkActive="active" class="nav-link">
            <i class="fas fa-user-shield"></i> Admin
          </a>
        </li>
        <li>
          <a routerLink="/financial-advisor" routerLinkActive="active" class="nav-link">
            <i class="fas fa-user-tie"></i> Financial Advisor
          </a>
        </li>
      </ul>
      
      <!-- User Section -->
      <div class="nav-footer">
        <button class="logout-btn" (click)="logout()">
          <i class="fas fa-sign-out-alt"></i> Logout
        </button>
      </div>
    </div>
  `,
  styles: [`
    /* Navigation component specific styles */
    .nav-link i {
      width: 20px;
      text-align: center;
    }
  `]
})
export class NavigationComponent {
  currentUser: any;
  
  constructor(private api: ApiService) {
    this.currentUser = this.api.getCurrentUser();
  }

  get unreadCount(): number {
    return this.api.getNotifications().filter(n => !n.isRead).length;
  }

  get isAdmin(): boolean {
    return this.currentUser?.role === 'admin';
  }

  getUserInitials(): string {
    if (!this.currentUser?.name) return 'U';
    const nameParts = this.currentUser.name.split(' ');
    const initials = nameParts[0][0] + (nameParts[1] ? nameParts[1][0] : '');
    return initials.toUpperCase();
  }
  
  logout() {
    this.api.logout();
    alert('Logged out');
  }
} 