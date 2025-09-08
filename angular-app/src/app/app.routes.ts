import { Routes } from '@angular/router';
import { DashboardPage } from './pages/dashboard/dashboard.page';
import { LoginPage } from './pages/login/login.page';
import { StokvelsPage } from './pages/stokvels/stokvels.page';
import { ContributionsPage } from './pages/contributions/contributions.page';
import { PayoutsPage } from './pages/payouts/payouts.page';
import { PaymentMethodsPage } from './pages/payment-methods/payment-methods.page';
import { ProfilePage } from './pages/profile/profile.page';
import { SettingsPage } from './pages/settings/settings.page';
import { MarketplacePage } from './pages/marketplace/marketplace.page';
import { RewardsPage } from './pages/rewards/rewards.page';
import { NotificationsPage } from './pages/notifications/notifications.page';
import { Component } from '@angular/core';
import { ActivitiesPage } from './pages/activities/activities.page';
import { Admin } from './pages/admin/admin';

@Component({
  selector: 'app-reports-placeholder',
  standalone: true,
  template: `
    <div style="padding:2rem">
      <h1 style="color:#fff">Reports</h1>
      <p style="color:rgba(255,255,255,0.8)">Reports functionality coming soon.</p>
    </div>
  `
})
  export class ReportsPlaceholder {}

export const routes: Routes = [
  { path: '', redirectTo: '/welcome', pathMatch: 'full' },
  { path: 'welcome', loadComponent: () => import('./pages/welcome/welcome.component').then(m => m.WelcomeComponent) },
  { path: 'dashboard', component: DashboardPage },
  { path: 'login', component: LoginPage },
  { path: 'register', loadComponent: () => import('./pages/register/register.page').then(m => m.RegisterPage) },
  { path: 'stokvels', component: StokvelsPage },
  { path: 'contributions', component: ContributionsPage },
  { path: 'payouts', component: PayoutsPage },
  { path: 'savings-goals', loadComponent: () => import('./pages/savings-goals/savings-goals.page').then(m => m.SavingsGoalsPage) },
  { path: 'payment-methods', component: PaymentMethodsPage },
  { path: 'profile', component: ProfilePage },
  { path: 'settings', component: SettingsPage },
  { path: 'marketplace', component: MarketplacePage },
  { path: 'rewards', component: RewardsPage },
  { path: 'notifications', component: NotificationsPage },
  { path: 'activities', component: ActivitiesPage },
  { path: 'financial-advisor', loadComponent: () => import('./pages/financial-advisor/financial-advisor.page').then(m => m.FinancialAdvisorPage) },
  { path: 'admin', component: Admin },
  // Temporary placeholder reports page used by dashboard quick action
  { path: 'reports', component: ReportsPlaceholder },
  // Add more routes as needed
];
