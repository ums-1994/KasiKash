import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-navigation',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <nav class="main-nav">
      <div class="nav-header">
        <div class="logo">
          <h2>KasiKash</h2>
        </div>
        <div class="user-info">
          <span class="username">{{ currentUser.name }}</span>
          <div class="user-avatar">
            <img [src]="currentUser.avatar" alt="Profile">
          </div>
        </div>
      </div>
      
      <ul class="nav-menu">
        <li>
          <a routerLink="/dashboard" routerLinkActive="active" class="nav-link">
            <i class="fas fa-home"></i>
            <span>Dashboard</span>
          </a>
        </li>
        <li>
          <a routerLink="/stokvels" routerLinkActive="active" class="nav-link">
            <i class="fas fa-users"></i>
            <span>Stokvels</span>
          </a>
        </li>
        <li>
          <a routerLink="/contributions" routerLinkActive="active" class="nav-link">
            <i class="fas fa-piggy-bank"></i>
            <span>Contributions</span>
          </a>
        </li>
        <li>
          <a routerLink="/marketplace" routerLinkActive="active" class="nav-link">
            <i class="fas fa-store"></i>
            <span>Marketplace</span>
          </a>
        </li>
        <li>
          <a routerLink="/rewards" routerLinkActive="active" class="nav-link">
            <i class="fas fa-gift"></i>
            <span>Rewards</span>
          </a>
        </li>
        <li>
          <a routerLink="/notifications" routerLinkActive="active" class="nav-link">
            <i class="fas fa-bell"></i>
            <span>Notifications</span>
            <span class="notification-badge" *ngIf="unreadCount > 0">{{ unreadCount }}</span>
          </a>
        </li>
        <li>
          <a routerLink="/profile" routerLinkActive="active" class="nav-link">
            <i class="fas fa-user"></i>
            <span>Profile</span>
          </a>
        </li>
        <li>
          <a routerLink="/settings" routerLinkActive="active" class="nav-link">
            <i class="fas fa-cog"></i>
            <span>Settings</span>
          </a>
        </li>
      </ul>
      
      <div class="nav-footer">
        <button class="logout-btn" (click)="logout()">
          <i class="fas fa-sign-out-alt"></i>
          <span>Logout</span>
        </button>
      </div>
    </nav>
  `,
  styles: [`
    /* Navigation Styles */
    .main-nav {
      width: 280px;
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(16px);
      border-right: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      flex-direction: column;
      position: fixed;
      height: 100vh;
      z-index: 1000;
    }

    .nav-header {
      padding: 2rem 1.5rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .logo h2 {
      background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
      font-weight: 800;
      font-size: 1.5rem;
    }

    .user-info {
      display: flex;
      align-items: center;
      margin-top: 1rem;
      gap: 0.75rem;
    }

    .username {
      font-weight: 500;
      color: rgba(255, 255, 255, 0.8);
    }

    .user-avatar img {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      border: 2px solid #7B61FF;
    }

    .nav-menu {
      list-style: none;
      padding: 1rem 0;
      flex: 1;
    }

    .nav-link {
      display: flex;
      align-items: center;
      padding: 0.75rem 1.5rem;
      color: rgba(255, 255, 255, 0.8);
      text-decoration: none;
      transition: all 0.3s ease;
      gap: 0.75rem;
      position: relative;
    }

    .nav-link:hover {
      color: var(--text-primary);
      background: rgba(85, 99, 222, 0.12);
      border-right: 3px solid var(--primary-color);
    }

    .nav-link.active {
      color: var(--primary-color);
      background: rgba(85, 99, 222, 0.12);
      border-right: 3px solid var(--primary-color);
    }

    .nav-link i {
      width: 20px;
      text-align: center;
    }

    .notification-badge {
      background: var(--accent-color);
      color: white;
      border-radius: 50%;
      width: 20px;
      height: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      font-weight: 600;
      margin-left: auto;
    }

    .nav-footer {
      padding: 1.5rem;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    .logout-btn {
      width: 100%;
      padding: 0.75rem;
      background: rgba(244, 67, 54, 0.1);
      color: #F44336;
      border: 1px solid rgba(244, 67, 54, 0.2);
      border-radius: 0.5rem;
      cursor: pointer;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
    }

    .logout-btn:hover {
      background: rgba(244, 67, 54, 0.2);
      border-color: #F44336;
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
  
  logout() {
    this.api.logout();
    alert('Logged out');
  }
} 