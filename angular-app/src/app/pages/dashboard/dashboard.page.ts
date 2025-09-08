import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="dashboard-container">
      <div class="dashboard-header">
        <h1>Welcome back, {{ userProfile.name }}!</h1>
        <p class="subtitle">Here's what's happening with your stokvels today</p>

        <!-- Backend connectivity status -->
        <div *ngIf="apiConnected; else mockNotice" style="margin-top:1rem">
          <span style="background: rgba(46,139,87,0.15); color:#6ee7b7; border:1px solid rgba(46,139,87,0.35); padding:0.5rem 0.75rem; border-radius:0.5rem; font-weight:600;">Backend Connected</span>
        </div>
        <ng-template #mockNotice>
          <div style="margin-top:1rem">
            <span style="background: rgba(245,166,35,0.15); color:#F5A623; border:1px solid rgba(245,166,35,0.35); padding:0.5rem 0.75rem; border-radius:0.5rem; font-weight:600;">Using mock data (start Flask API to enable live data)</span>
          </div>
        </ng-template>
      </div>
      
      <!-- Quick Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-users"></i>
          </div>
          <div class="stat-content">
            <h3>Active Stokvels</h3>
            <p class="stat-value">{{ stats.activeStokvels }}</p>
            <span class="stat-change positive">+{{ stats.stokvelGrowth }}%</span>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-piggy-bank"></i>
          </div>
          <div class="stat-content">
            <h3>Total Savings</h3>
            <p class="stat-value">R{{ stats.totalSavings | number:'1.0-0' }}</p>
            <span class="stat-change positive">+{{ stats.savingsGrowth }}%</span>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-chart-line"></i>
          </div>
          <div class="stat-content">
            <h3>This Month</h3>
            <p class="stat-value">R{{ stats.thisMonthContribution | number:'1.0-0' }}</p>
            <span class="stat-change positive">+{{ stats.monthlyGrowth }}%</span>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-gift"></i>
          </div>
          <div class="stat-content">
            <h3>Reward Points</h3>
            <p class="stat-value">{{ stats.rewardPoints }}</p>
            <span class="stat-change positive">+{{ stats.pointsGrowth }}%</span>
          </div>
        </div>
      </div>
      
      <!-- Main Content Grid -->
      <div class="dashboard-grid">
        <!-- Recent Activities -->
        <div class="dashboard-card">
          <div class="card-header">
            <h3>Recent Activities</h3>
            <a routerLink="/activities" class="view-all">View All</a>
          </div>
          <div class="activities-list">
            <div class="activity-item" *ngFor="let activity of recentActivities">
              <div class="activity-icon" [class]="activity.type">
                <i [class]="getActivityIcon(activity.type)"></i>
              </div>
              <div class="activity-content">
                <h4>{{ activity.title }}</h4>
                <p>{{ activity.description }}</p>
                <span class="activity-time">{{ activity.time }}</span>
              </div>
              <div class="activity-amount" *ngIf="activity.amount">
                R{{ activity.amount }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- Upcoming Contributions -->
        <div class="dashboard-card">
          <div class="card-header">
            <h3>Upcoming Contributions</h3>
            <a routerLink="/contributions" class="view-all">View All</a>
          </div>
          <div class="contributions-list">
            <div class="contribution-item" *ngFor="let contribution of upcomingContributions">
              <div class="contribution-info">
                <h4>{{ contribution.stokvelName }}</h4>
                <p>Due: {{ contribution.dueDate }}</p>
              </div>
              <div class="contribution-amount">
                R{{ contribution.amount }}
              </div>
              <button class="btn-primary btn-small" (click)="payContribution(contribution)">Pay Now</button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Quick Actions -->
      <div class="quick-actions">
        <h3>Quick Actions</h3>
        <div class="actions-grid">
          <button class="action-btn" (click)="makeContribution()">
            <i class="fas fa-plus"></i>
            <span>Make Contribution</span>
          </button>
          <button class="action-btn" (click)="createStokvel()">
            <i class="fas fa-users"></i>
            <span>Create Stokvel</span>
          </button>
          <button class="action-btn" (click)="inviteMember()">
            <i class="fas fa-user-plus"></i>
            <span>Invite Member</span>
          </button>
          <button class="action-btn" (click)="viewReports()">
            <i class="fas fa-chart-bar"></i>
            <span>View Reports</span>
          </button>
        </div>
      </div>

      <!-- Contribution Modal -->
      <div class="modal-overlay" *ngIf="showContributionModal" (click)="closeContributionModal()">
        <div class="modal-content" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <h3>Make Contribution</h3>
            <button class="close-btn" (click)="closeContributionModal()">×</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>Select Stokvel</label>
              <select [(ngModel)]="selectedStokvel" class="form-control">
                <option value="">Choose a stokvel...</option>
                <option *ngFor="let stokvel of availableStokvels" [value]="stokvel.id">
                  {{ stokvel.name }} - R{{ stokvel.contributionAmount }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>Amount (R)</label>
              <input type="number" [(ngModel)]="contributionAmount" class="form-control" placeholder="Enter amount">
            </div>
            <div class="form-group">
              <label>Payment Method</label>
              <select [(ngModel)]="paymentMethod" class="form-control">
                <option value="bank">Bank Transfer</option>
                <option value="card">Credit/Debit Card</option>
                <option value="mobile">Mobile Money</option>
              </select>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" (click)="closeContributionModal()">Cancel</button>
            <button class="btn-primary" (click)="submitContribution()" [disabled]="!selectedStokvel || !contributionAmount">
              Submit Contribution
            </button>
          </div>
        </div>
      </div>

      <!-- Create Stokvel Modal -->
      <div class="modal-overlay" *ngIf="showStokvelModal" (click)="closeStokvelModal()">
        <div class="modal-content" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <h3>Create New Stokvel</h3>
            <button class="close-btn" (click)="closeStokvelModal()">×</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>Stokvel Name</label>
              <input type="text" [(ngModel)]="newStokvel.name" class="form-control" placeholder="Enter stokvel name">
            </div>
            <div class="form-group">
              <label>Description</label>
              <textarea [(ngModel)]="newStokvel.description" class="form-control" placeholder="Describe your stokvel"></textarea>
            </div>
            <div class="form-group">
              <label>Monthly Contribution (R)</label>
              <input type="number" [(ngModel)]="newStokvel.contributionAmount" class="form-control" placeholder="Enter amount">
            </div>
            <div class="form-group">
              <label>Meeting Day</label>
              <select [(ngModel)]="newStokvel.meetingDay" class="form-control">
                <option value="">Select day...</option>
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
            <button class="btn-secondary" (click)="closeStokvelModal()">Cancel</button>
            <button class="btn-primary" (click)="submitStokvel()" [disabled]="!newStokvel.name || !newStokvel.contributionAmount">
              Create Stokvel
            </button>
          </div>
        </div>
      </div>

      <!-- Invite Member Modal -->
      <div class="modal-overlay" *ngIf="showInviteModal" (click)="closeInviteModal()">
        <div class="modal-content" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <h3>Invite Member</h3>
            <button class="close-btn" (click)="closeInviteModal()">×</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>Select Stokvel</label>
              <select [(ngModel)]="inviteStokvel" class="form-control">
                <option value="">Choose a stokvel...</option>
                <option *ngFor="let stokvel of availableStokvels" [value]="stokvel.id">
                  {{ stokvel.name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>Email Address</label>
              <input type="email" [(ngModel)]="inviteEmail" class="form-control" placeholder="Enter email address">
            </div>
            <div class="form-group">
              <label>Phone Number</label>
              <input type="tel" [(ngModel)]="invitePhone" class="form-control" placeholder="Enter phone number">
            </div>
            <div class="form-group">
              <label>Personal Message (Optional)</label>
              <textarea [(ngModel)]="inviteMessage" class="form-control" placeholder="Add a personal message"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" (click)="closeInviteModal()">Cancel</button>
            <button class="btn-primary" (click)="submitInvite()" [disabled]="!inviteStokvel || !inviteEmail">
              Send Invitation
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    /* Dashboard Styles */
    .dashboard-container {
      max-width: 1400px;
      margin: 0 auto;
    }

    .dashboard-header {
      text-align: center;
      margin-bottom: 2rem;
    }

    .dashboard-header h1 {
      font-size: 2.5rem;
      font-weight: 800;
      background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.5rem;
    }

    .subtitle {
      color: rgba(255, 255, 255, 0.7);
      font-size: 1.125rem;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }

    .stat-card {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 1rem;
      padding: 1.5rem;
      display: flex;
      align-items: center;
      gap: 1rem;
      transition: all 0.3s ease;
    }

    .stat-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
      border-color: var(--primary-color);
    }

    .stat-icon {
      width: 60px;
      height: 60px;
      background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.5rem;
      color: white;
    }

    .stat-content h3 {
      color: rgba(255, 255, 255, 0.7);
      font-size: 0.875rem;
      font-weight: 500;
      margin-bottom: 0.5rem;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .stat-value {
      font-size: 2rem;
      font-weight: 800;
      color: #fff;
      margin-bottom: 0.25rem;
    }

    .stat-change {
      font-size: 0.875rem;
      font-weight: 600;
      padding: 0.25rem 0.5rem;
      border-radius: 0.375rem;
    }

    .stat-change.positive {
      background: rgba(76, 175, 80, 0.2);
      color: var(--success-color);
    }

    .dashboard-grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 2rem;
      margin-bottom: 2rem;
    }

    .dashboard-card {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 1rem;
      padding: 1.5rem;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .card-header h3 {
      color: #fff;
      font-weight: 600;
    }

    .view-all {
      color: var(--primary-color);
      text-decoration: none;
      font-size: 0.875rem;
      font-weight: 500;
      transition: all 0.3s ease;
    }

    .view-all:hover {
      color: var(--secondary-color);
    }

    .activities-list {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .activity-item {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 0.5rem;
      transition: all 0.3s ease;
    }

    .activity-item:hover {
      background: rgba(255, 255, 255, 0.05);
    }

    .activity-icon {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.25rem;
    }

    .activity-icon.contribution {
      background: rgba(76, 175, 80, 0.2);
      color: var(--success-color);
    }

    .activity-icon.stokvel {
      background: rgba(33, 150, 243, 0.2);
      color: var(--info-color);
    }

    .activity-icon.reward {
      background: rgba(255, 152, 0, 0.2);
      color: #FF9800;
    }

    .activity-icon.payout {
      background: rgba(156, 39, 176, 0.2);
      color: #9C27B0;
    }

    .activity-content {
      flex: 1;
    }

    .activity-content h4 {
      color: #fff;
      font-weight: 600;
      margin-bottom: 0.25rem;
    }

    .activity-content p {
      color: rgba(255, 255, 255, 0.7);
      font-size: 0.875rem;
      margin-bottom: 0.25rem;
    }

    .activity-time {
      font-size: 0.75rem;
      color: rgba(255, 255, 255, 0.5);
    }

    .activity-amount {
      font-weight: 600;
      color: var(--primary-color);
      font-size: 1.125rem;
    }

    .contributions-list {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .contribution-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 1rem;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 0.5rem;
      border-left: 4px solid var(--primary-color);
    }

    .contribution-info h4 {
      color: #fff;
      font-weight: 600;
      margin-bottom: 0.25rem;
    }

    .contribution-info p {
      color: rgba(255, 255, 255, 0.7);
      font-size: 0.875rem;
    }

    .contribution-amount {
      font-weight: 700;
      color: var(--primary-color);
      font-size: 1.25rem;
    }

    .quick-actions {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 1rem;
      padding: 1.5rem;
    }

    .quick-actions h3 {
      color: #fff;
      font-weight: 600;
      margin-bottom: 1.5rem;
    }

    .actions-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
    }

    .action-btn {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 0.5rem;
      padding: 1.5rem;
      color: #fff;
      cursor: pointer;
      transition: all 0.3s ease;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.75rem;
      text-align: center;
    }

    .action-btn:hover {
      background: rgba(255, 255, 255, 0.05);
      border-color: var(--primary-color);
      transform: translateY(-2px);
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }

    .action-btn i {
      font-size: 2rem;
      color: var(--primary-color);
    }

    .action-btn span {
      font-weight: 500;
    }

    .btn-primary {
      background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
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
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }

    .btn-small {
      padding: 0.5rem 1rem;
      font-size: 0.875rem;
    }

    /* Modal Styles */
    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.8);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      backdrop-filter: blur(10px);
    }

    .modal-content {
      background: rgba(30, 30, 30, 0.95);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 1rem;
      width: 90%;
      max-width: 500px;
      max-height: 90vh;
      overflow-y: auto;
      backdrop-filter: blur(20px);
    }

    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.5rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .modal-header h3 {
      color: white;
      font-size: 1.25rem;
      font-weight: 600;
      margin: 0;
    }

    .close-btn {
      background: none;
      border: none;
      color: rgba(255, 255, 255, 0.7);
      font-size: 1.5rem;
      cursor: pointer;
      padding: 0;
      width: 30px;
      height: 30px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      transition: all 0.3s ease;
    }

    .close-btn:hover {
      background: rgba(255, 255, 255, 0.1);
      color: white;
    }

    .modal-body {
      padding: 1.5rem;
    }

    .modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: 1rem;
      padding: 1.5rem;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    .form-group {
      margin-bottom: 1.5rem;
    }

    .form-group label {
      display: block;
      color: white;
      font-weight: 500;
      margin-bottom: 0.5rem;
    }

    .form-control {
      width: 100%;
      padding: 0.75rem;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 0.5rem;
      color: white;
      font-size: 0.875rem;
      transition: all 0.3s ease;
    }

    .form-control:focus {
      outline: none;
      border-color: var(--primary-color);
      box-shadow: 0 0 0 3px rgba(85, 99, 222, 0.12);
    }

    .form-control::placeholder {
      color: rgba(255, 255, 255, 0.5);
    }

    textarea.form-control {
      resize: vertical;
      min-height: 80px;
    }

    @media (max-width: 1024px) {
      .dashboard-grid {
        grid-template-columns: 1fr;
      }
      
      .stats-grid {
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      }
      
      .actions-grid {
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      }
    }

    @media (max-width: 768px) {
      .dashboard-header h1 {
        font-size: 2rem;
      }
      
      .stats-grid {
        grid-template-columns: 1fr;
      }
      
      .actions-grid {
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      }
      
      .stat-card {
        flex-direction: column;
        text-align: center;
      }
      
      .modal-content {
        width: 95%;
        margin: 1rem;
      }
    }
  `]
})
export class DashboardPage implements OnInit {
  userProfile = {
    name: 'John Doe'
  };
  apiConnected = false;
  
  stats = {
    activeStokvels: 3,
    totalSavings: 45000,
    thisMonthContribution: 1500,
    rewardPoints: 1250,
    stokvelGrowth: 12.5,
    savingsGrowth: 8.3,
    monthlyGrowth: 15.2,
    pointsGrowth: 22.1
  };
  
  recentActivities = [
    {
      type: 'contribution',
      title: 'Contribution Made',
      description: 'R500 contributed to Family Savings stokvel',
      time: '2 hours ago',
      amount: 500
    },
    {
      type: 'stokvel',
      title: 'New Member Joined',
      description: 'Sarah Johnson joined Family Savings stokvel',
      time: '1 day ago'
    },
    {
      type: 'reward',
      title: 'Points Earned',
      description: 'Earned 100 points for monthly contribution',
      time: '2 days ago',
      amount: 100
    },
    {
      type: 'payout',
      title: 'Payout Requested',
      description: 'R2000 payout requested from Business Investment',
      time: '3 days ago',
      amount: 2000
    }
  ];
  
  upcomingContributions = [
    {
      stokvelName: 'Family Savings',
      dueDate: '15 Dec 2024',
      amount: 500
    },
    {
      stokvelName: 'Business Investment',
      dueDate: '20 Dec 2024',
      amount: 1000
    }
  ];

  // Modal states
  showContributionModal = false;
  showStokvelModal = false;
  showInviteModal = false;

  // Contribution modal data
  selectedStokvel = '';
  contributionAmount = 0;
  paymentMethod = 'bank';

  // Create stokvel modal data
  newStokvel = {
    name: '',
    description: '',
    contributionAmount: 0,
    meetingDay: ''
  };

  // Invite modal data
  inviteStokvel = '';
  inviteEmail = '';
  invitePhone = '';
  inviteMessage = '';

  // Available stokvels for dropdowns
  availableStokvels = [
    { id: '1', name: 'Family Savings', contributionAmount: 500 },
    { id: '2', name: 'Business Investment', contributionAmount: 1000 },
    { id: '3', name: 'Education Fund', contributionAmount: 750 }
  ];
  
  constructor(private apiService: ApiService, private router: Router) {}
  
  ngOnInit(): void {
    this.loadDashboardData();
  }
  
  loadDashboardData() {
    this.apiService.getAdminStats().subscribe({
      next: (data) => {
        this.apiConnected = !data?.note; // note exists only on mock fallback
        console.log('Dashboard data loaded:', data);
      },
      error: (err) => {
        console.error('Error loading dashboard data:', err);
      }
    });
  }
  
  getActivityIcon(type: string): string {
    const iconMap: { [key: string]: string } = {
      contribution: 'fas fa-plus-circle',
      stokvel: 'fas fa-users',
      reward: 'fas fa-gift',
      payout: 'fas fa-money-bill-wave'
    };
    return iconMap[type] || 'fas fa-info-circle';
  }
  
  // Quick Actions Implementation
  makeContribution() {
    this.showContributionModal = true;
  }

  createStokvel() {
    this.showStokvelModal = true;
  }

  inviteMember() {
    this.showInviteModal = true;
  }

  viewReports() {
    // Navigate to reports page (you can create this page later)
    this.router.navigate(['/reports']);
  }

  // Modal close functions
  closeContributionModal() {
    this.showContributionModal = false;
    this.selectedStokvel = '';
    this.contributionAmount = 0;
    this.paymentMethod = 'bank';
  }

  closeStokvelModal() {
    this.showStokvelModal = false;
    this.newStokvel = {
      name: '',
      description: '',
      contributionAmount: 0,
      meetingDay: ''
    };
  }

  closeInviteModal() {
    this.showInviteModal = false;
    this.inviteStokvel = '';
    this.inviteEmail = '';
    this.invitePhone = '';
    this.inviteMessage = '';
  }

  // Submit functions
  submitContribution() {
    if (this.selectedStokvel && this.contributionAmount) {
      const created = this.apiService.addContribution({
        stokvelId: this.selectedStokvel,
        amount: this.contributionAmount,
        method: this.paymentMethod
      });

      alert(`Successfully contributed R${this.contributionAmount} to ${created.stokvelName}!`);
      this.closeContributionModal();
      
      // Update the stats
      this.stats.thisMonthContribution += this.contributionAmount;
      this.stats.totalSavings += this.contributionAmount;
      
      // Add to recent activities
      this.recentActivities.unshift({
        type: 'contribution',
        title: 'Contribution Made',
        description: `R${this.contributionAmount} contributed to ${created.stokvelName}`,
        time: 'Just now',
        amount: this.contributionAmount
      });
    }
  }

  submitStokvel() {
    if (this.newStokvel.name && this.newStokvel.contributionAmount) {
      const created = this.apiService.createStokvel({
        name: this.newStokvel.name,
        description: this.newStokvel.description,
        contributionAmount: this.newStokvel.contributionAmount,
        meetingDay: this.newStokvel.meetingDay
      });

      alert(`Successfully created "${created.name}" stokvel!`);
      this.closeStokvelModal();
      
      // Update the stats
      this.stats.activeStokvels += 1;
      
      // Add to recent activities
      this.recentActivities.unshift({
        type: 'stokvel',
        title: 'New Stokvel Created',
        description: `Created "${created.name}" stokvel`,
        time: 'Just now'
      });
    }
  }

  submitInvite() {
    if (this.inviteStokvel && this.inviteEmail) {
      // Here you would typically make an API call
      console.log('Sending invitation:', {
        stokvelId: this.inviteStokvel,
        email: this.inviteEmail,
        phone: this.invitePhone,
        message: this.inviteMessage
      });

      // Simulate API call
      setTimeout(() => {
        alert(`Invitation sent successfully to ${this.inviteEmail}!`);
        this.closeInviteModal();
        
        // Add to recent activities
        this.recentActivities.unshift({
          type: 'stokvel',
          title: 'Member Invited',
          description: `Invitation sent to ${this.inviteEmail}`,
          time: 'Just now'
        });
      }, 1000);
    }
  }

  // Pay contribution from upcoming contributions
  payContribution(contribution: any) {
    this.selectedStokvel = this.availableStokvels.find(s => s.name === contribution.stokvelName)?.id || '';
    this.contributionAmount = contribution.amount;
    this.showContributionModal = true;
  }
}

