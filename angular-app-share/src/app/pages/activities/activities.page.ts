import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-activities',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="activities-container">
      <div class="header">
        <h1>All Activities</h1>
      </div>

      <div class="activities-list">
        <div class="activity-item" *ngFor="let activity of activities">
          <div class="activity-icon" [class]="activity.type">
            <i [class]="getIcon(activity.type)"></i>
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
  `,
  styles: [`
    .activities-container { padding: 2rem; }
    .header h1 { color: #fff; margin-bottom: 1rem; }
    .activities-list { display: flex; flex-direction: column; gap: 1rem; }
    .activity-item { display:flex;align-items:center;gap:1rem;padding:1rem;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:0.5rem }
    .activity-icon { width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff }
    .activity-icon.contribution{background:linear-gradient(135deg, var(--success-color), #1B5E20)}
    .activity-icon.stokvel{background:linear-gradient(135deg, var(--primary-color), var(--primary-dark))}
    .activity-icon.reward{background:linear-gradient(135deg, var(--warning-color), #D0873A)}
    .activity-icon.payout{background:linear-gradient(135deg, var(--error-color), #C44536)}
    .activity-content h4 { color: var(--text-primary); margin:0 }
    .activity-content p { color: var(--text-secondary); margin:.25rem 0 }
    .activity-time { color: var(--text-muted); font-size:.85rem }
    .activity-amount { color: var(--success-color); font-weight:600 }
  `]
})
export class ActivitiesPage implements OnInit {
  activities: any[] = [];

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.activities = this.api.getActivities();
  }

  getIcon(type: string): string {
    const iconMap: Record<string,string> = {
      contribution: 'fas fa-plus-circle',
      stokvel: 'fas fa-users',
      reward: 'fas fa-gift',
      payout: 'fas fa-money-bill-wave'
    };
    return iconMap[type] || 'fas fa-info-circle';
  }
}


