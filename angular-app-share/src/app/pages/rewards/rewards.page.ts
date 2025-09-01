import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-rewards',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="rewards-container">
      <div class="header">
        <h1>Rewards & Loyalty</h1>
        <div class="points-summary">
          <span class="points-label">Total Points:</span>
          <span class="points-value">{{ totalPoints }}</span>
        </div>
      </div>
      
      <div class="rewards-grid">
        <div class="reward-card" *ngFor="let reward of rewards">
          <div class="reward-image">
            <img [src]="reward.image" [alt]="reward.name">
          </div>
          <div class="reward-info">
            <h3>{{ reward.name }}</h3>
            <p class="description">{{ reward.description }}</p>
            <p class="points-required">{{ reward.pointsRequired }} points</p>
          </div>
          <div class="reward-actions">
            <button class="btn-primary" 
                    [disabled]="totalPoints < reward.pointsRequired"
                    (click)="redeemReward(reward)">
              {{ totalPoints >= reward.pointsRequired ? 'Redeem' : 'Not Enough Points' }}
            </button>
          </div>
        </div>
      </div>
      
      <div class="earned-rewards">
        <h2>Recently Earned</h2>
        <div class="earned-item" *ngFor="let earned of earnedRewards">
          <div class="earned-info">
            <span class="reward-name">{{ earned.rewardName }}</span>
            <span class="earned-date">{{ earned.earnedDate }}</span>
          </div>
          <span class="points-earned">+{{ earned.points }} points</span>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .rewards-container { padding: 2rem; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
    .header h1 { color: #fff; }
    .points-summary { text-align: right; }
    .points-label { color: rgba(255,255,255,0.7); margin-right: 0.5rem; }
    .points-value { color: var(--primary-color); font-size: 1.5rem; font-weight: 700; }
    .rewards-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
    .reward-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 1rem; padding: 1.5rem; }
    .reward-image img { width: 100%; height: 150px; object-fit: cover; border-radius: 0.5rem; margin-bottom: 1rem; }
    .reward-info h3 { color: #fff; margin-bottom: 0.5rem; }
    .description { color: rgba(255,255,255,0.7); margin-bottom: 0.5rem; }
    .points-required { color: var(--warning-color); font-weight: 600; margin-bottom: 1rem; }
    .reward-actions { text-align: center; }
    .btn-primary { background: var(--primary-color); color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; width: 100%; }
    .btn-primary:disabled { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.5); cursor: not-allowed; }
    .earned-rewards h2 { color: #fff; margin-bottom: 1rem; }
    .earned-item { display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 0.5rem; padding: 1rem; margin-bottom: 0.5rem; }
    .earned-info { display: flex; flex-direction: column; }
    .reward-name { color: #fff; font-weight: 600; }
    .earned-date { color: rgba(255,255,255,0.6); font-size: 0.875rem; }
    .points-earned { color: var(--success-color); font-weight: 600; }
  `]
})
export class RewardsPage {
  totalPoints = 0;
  rewards: any[] = [];
  earnedRewards: any[] = [];

  constructor(private api: ApiService) {
    this.totalPoints = this.api.getPoints();
    this.rewards = this.api.getRewardsCatalog();
    this.earnedRewards = this.api.getEarnedRewards();
  }

  redeemReward(reward: any) {
    const result = this.api.redeemReward(reward.id);
    this.totalPoints = result.points;
    this.earnedRewards = this.api.getEarnedRewards();
    alert(result.message);
  }
}