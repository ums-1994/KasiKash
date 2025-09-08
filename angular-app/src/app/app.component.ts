import { Component, inject } from '@angular/core';
import { Router, RouterOutlet, NavigationEnd, RouterModule } from '@angular/router';
import { NgIf } from '@angular/common';
import { NavigationComponent } from './components/navigation/navigation.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterModule, NavigationComponent, NgIf],
  template: `
    <div class="app-container" [class.no-sidebar]="!showSidebar">
      <app-navigation *ngIf="showSidebar"></app-navigation>
      <div class="ml-64" *ngIf="showSidebar">
        <!-- Top Bar with Profile and Notifications -->
        <div class="top-bar">
          <div class="flex items-center justify-between w-full px-6 py-4">
            <h2 class="text-xl page-title">Dashboard</h2>
            <div class="flex items-center space-x-6">
              <!-- Theme Toggle Button -->
              <button id="theme-toggle" class="theme-toggle p-2 rounded-lg transition-all duration-300">
                <i id="theme-icon" class="fas fa-sun text-xl"></i>
              </button>
              <a routerLink="/notifications" id="notification-icon" class="notification-icon relative">
                <i class="fa-solid fa-bell w-6 h-6 text-xl"></i>
                <span id="notification-badge" class="notification-badge absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full text-xs font-bold text-white hidden">
                  0
                </span>
              </a>
              <a routerLink="/profile" class="profile-icon">
                <i class="fa-solid fa-user-circle w-6 h-6 text-xl"></i>
              </a>
            </div>
          </div>
        </div>
        <main class="p-6 dashboard-content">
          <div class="page-background"></div>
          <div class="page-overlay"></div>
          <div class="content-container">
            <router-outlet />
          </div>
        </main>
      </div>
      <main class="main-content" [class.no-sidebar]="!showSidebar" *ngIf="!showSidebar">
        <div class="page-background"></div>
        <div class="page-overlay"></div>
        <div class="content-container">
          <router-outlet />
        </div>
      </main>
    </div>
  `,
  styles: [`
    /* App Component Styles */
    .app-container {
      display: flex;
      min-height: 100vh;
    }

    .main-content {
      flex: 1;
      margin-left: 280px;
      padding: 2rem;
      min-height: 100vh;
    }

    .main-content.no-sidebar {
      margin-left: 0;
      padding: 0;
    }

    .app-container.no-sidebar {
      display: block;
    }

    .top-bar {
      position: sticky;
      top: 0;
      z-index: 10;
      background: linear-gradient(
        135deg,
        rgba(46, 139, 87, 0.35) 0%,
        rgba(0, 152, 121, 0.35) 60%,
        rgba(245, 166, 35, 0.12) 100%
      );
      backdrop-filter: blur(18px);
      -webkit-backdrop-filter: blur(18px);
      border-bottom: 1px solid rgba(255, 255, 255, 0.18);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
    }

    .page-title {
      color: #ffffff;
      text-shadow: 0 1px 2px rgba(0, 0, 0, 0.35), 0 0 16px rgba(255, 255, 255, 0.18);
      font-weight: 800;
      letter-spacing: -0.5px;
    }

    .notification-icon, .profile-icon {
      color: rgba(255, 255, 255, 0.9);
      transition: all 0.3s ease;
    }

    .notification-icon:hover, .profile-icon:hover {
      color: #F5F5F5;
      transform: translateY(-1px);
      filter: drop-shadow(0 0 8px rgba(245, 166, 35, 0.45));
    }

    .notification-badge {
      background: linear-gradient(135deg, #2E8B57, #009879);
      box-shadow: 0 0 10px rgba(0, 152, 121, 0.45);
    }

    /* Theme Toggle Button */
    .theme-toggle {
      background: rgba(255, 255, 255, 0.12);
      border: 1px solid rgba(255, 255, 255, 0.25);
      color: rgba(255, 255, 255, 0.9);
      transition: all 0.3s ease;
    }

    .theme-toggle:hover {
      background: rgba(255, 255, 255, 0.22);
      color: #ffffff;
      transform: translateY(-1px);
    }

    /* Responsive Design */
    @media (max-width: 1024px) {
      .main-content {
        margin-left: 240px;
      }
    }

    @media (max-width: 768px) {
      .main-content {
        margin-left: 0;
        padding: 1rem;
      }
    }
  `]
})
export class AppComponent {
  title = 'angular-app';
  private readonly router = inject(Router);
  showSidebar = true;

  constructor() {
    this.showSidebar = !this.shouldHideSidebar(this.router.url);
    this.router.events.subscribe(e => {
      if (e instanceof NavigationEnd) {
        this.showSidebar = !this.shouldHideSidebar(e.urlAfterRedirects);
      }
    });
  }

  private shouldHideSidebar(url: string): boolean {
    return url.startsWith('/welcome') || url.startsWith('/login') || url.startsWith('/register');
  }
} 