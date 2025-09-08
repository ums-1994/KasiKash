import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="admin-page">
      <!-- Header Section -->
      <div class="header-section mb-8">
        <h1 class="text-4xl font-bold text-gradient mb-4">Admin Dashboard</h1>
        <p class="text-gray-300 text-lg">Manage users, stokvels, and system settings</p>
      </div>

      <!-- Admin Stats -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="glass-card p-6 rounded-xl">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-2xl font-bold text-white">{{ totalUsers }}</h3>
              <p class="text-gray-400">Total Users</p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-blue-400 to-purple-500 rounded-full flex items-center justify-center">
              <i class="fas fa-users text-white text-xl"></i>
            </div>
          </div>
        </div>

        <div class="glass-card p-6 rounded-xl">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-2xl font-bold text-white">{{ totalStokvels }}</h3>
              <p class="text-gray-400">Active Stokvels</p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center">
              <i class="fas fa-hand-holding-usd text-white text-xl"></i>
            </div>
          </div>
        </div>

        <div class="glass-card p-6 rounded-xl">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-2xl font-bold text-white">R {{ totalTransactions | number:'1.0-0' }}</h3>
              <p class="text-gray-400">Total Volume</p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
              <i class="fas fa-chart-bar text-white text-xl"></i>
            </div>
          </div>
        </div>

        <div class="glass-card p-6 rounded-xl">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-2xl font-bold text-white">{{ pendingApprovals }}</h3>
              <p class="text-gray-400">Pending Approvals</p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-red-400 to-pink-500 rounded-full flex items-center justify-center">
              <i class="fas fa-clock text-white text-xl"></i>
            </div>
          </div>
        </div>
      </div>

      <!-- Admin Actions Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <!-- User Management -->
        <div class="glass-card p-6 rounded-xl">
          <h2 class="text-2xl font-bold text-white mb-6 flex items-center">
            <i class="fas fa-user-cog mr-3 text-blue-400"></i>
            User Management
          </h2>
          
          <div class="space-y-4">
            <div class="admin-action-item p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
              <div class="flex items-center justify-between">
                <div>
                  <h4 class="text-lg font-semibold text-white">User Accounts</h4>
                  <p class="text-gray-400 text-sm">Manage user accounts and permissions</p>
                </div>
                <button class="btn-primary px-4 py-2 text-sm">Manage</button>
              </div>
            </div>

            <div class="admin-action-item p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
              <div class="flex items-center justify-between">
                <div>
                  <h4 class="text-lg font-semibold text-white">KYC Verification</h4>
                  <p class="text-gray-400 text-sm">Review and approve KYC documents</p>
                </div>
                <button class="btn-primary px-4 py-2 text-sm">Review</button>
              </div>
            </div>

            <div class="admin-action-item p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
              <div class="flex items-center justify-between">
                <div>
                  <h4 class="text-lg font-semibold text-white">User Reports</h4>
                  <p class="text-gray-400 text-sm">Generate user activity reports</p>
                </div>
                <button class="btn-primary px-4 py-2 text-sm">Generate</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Stokvel Management -->
        <div class="glass-card p-6 rounded-xl">
          <h2 class="text-2xl font-bold text-white mb-6 flex items-center">
            <i class="fas fa-hand-holding-usd mr-3 text-green-400"></i>
            Stokvel Management
          </h2>
          
          <div class="space-y-4">
            <div class="admin-action-item p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
              <div class="flex items-center justify-between">
                <div>
                  <h4 class="text-lg font-semibold text-white">Stokvel Registry</h4>
                  <p class="text-gray-400 text-sm">View and manage all registered stokvels</p>
                </div>
                <button class="btn-primary px-4 py-2 text-sm">View All</button>
              </div>
            </div>

            <div class="admin-action-item p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
              <div class="flex items-center justify-between">
                <div>
                  <h4 class="text-lg font-semibold text-white">Transaction Monitoring</h4>
                  <p class="text-gray-400 text-sm">Monitor suspicious transactions</p>
                </div>
                <button class="btn-primary px-4 py-2 text-sm">Monitor</button>
              </div>
            </div>

            <div class="admin-action-item p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
              <div class="flex items-center justify-between">
                <div>
                  <h4 class="text-lg font-semibold text-white">Compliance Reports</h4>
                  <p class="text-gray-400 text-sm">Generate regulatory compliance reports</p>
                </div>
                <button class="btn-primary px-4 py-2 text-sm">Generate</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- System Settings -->
      <div class="glass-card p-6 rounded-xl">
        <h2 class="text-2xl font-bold text-white mb-6 flex items-center">
          <i class="fas fa-cogs mr-3 text-purple-400"></i>
          System Settings
        </h2>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div class="setting-item p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
            <h4 class="text-lg font-semibold text-white mb-2">Interest Rates</h4>
            <p class="text-gray-400 text-sm mb-4">Configure interest rates for different account types</p>
            <button class="btn-secondary w-full text-sm">Configure</button>
          </div>

          <div class="setting-item p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
            <h4 class="text-lg font-semibold text-white mb-2">Transaction Limits</h4>
            <p class="text-gray-400 text-sm mb-4">Set daily and monthly transaction limits</p>
            <button class="btn-secondary w-full text-sm">Set Limits</button>
          </div>

          <div class="setting-item p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
            <h4 class="text-lg font-semibold text-white mb-2">Notification Settings</h4>
            <p class="text-gray-400 text-sm mb-4">Configure system-wide notification preferences</p>
            <button class="btn-secondary w-full text-sm">Configure</button>
          </div>

          <div class="setting-item p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
            <h4 class="text-lg font-semibold text-white mb-2">Backup & Recovery</h4>
            <p class="text-gray-400 text-sm mb-4">Manage system backups and recovery procedures</p>
            <button class="btn-secondary w-full text-sm">Manage</button>
          </div>

          <div class="setting-item p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
            <h4 class="text-lg font-semibold text-white mb-2">Security Settings</h4>
            <p class="text-gray-400 text-sm mb-4">Configure security policies and access controls</p>
            <button class="btn-secondary w-full text-sm">Configure</button>
          </div>

          <div class="setting-item p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
            <h4 class="text-lg font-semibold text-white mb-2">API Management</h4>
            <p class="text-gray-400 text-sm mb-4">Manage API keys and third-party integrations</p>
            <button class="btn-secondary w-full text-sm">Manage</button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .admin-page {
      padding: 2rem;
      min-height: 100vh;
    }

    .glass-card {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
      transition: all 0.3s ease;
    }

    .glass-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
    }

    .text-gradient {
      background: linear-gradient(90deg, #7B61FF, #61DAFB);
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .btn-primary {
      background: linear-gradient(135deg, #7B61FF, #61DAFB);
      color: white;
      border: none;
      padding: 0.75rem 1.5rem;
      border-radius: 0.5rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(123, 97, 255, 0.3);
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.1);
      color: white;
      border: 1px solid rgba(255, 255, 255, 0.2);
      padding: 0.5rem 1rem;
      border-radius: 0.5rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.2);
    }

    .admin-action-item {
      transition: all 0.3s ease;
    }

    .admin-action-item:hover {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(123, 97, 255, 0.3);
    }

    .setting-item {
      transition: all 0.3s ease;
    }

    .setting-item:hover {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(123, 97, 255, 0.3);
    }
  `]
})
export class Admin {
  totalUsers = 1247;
  totalStokvels = 89;
  totalTransactions = 2450000;
  pendingApprovals = 12;
}
