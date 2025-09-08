import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-rewards',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="rewards-page">
      <div class="page-background"></div>
      <div class="page-overlay"></div>
      
    <div class="rewards-container">
      <div class="header">
        <h1>Rewards & Loyalty</h1>
        <div class="points-summary">
            <div class="points-card">
              <i class="fas fa-star"></i>
              <div class="points-info">
                <span class="points-label">Total Points</span>
          <span class="points-value">{{ totalPoints }}</span>
              </div>
            </div>
        </div>
      </div>
      
        <div class="rewards-section">
          <h2>Available Rewards</h2>
      <div class="rewards-grid">
        <div class="reward-card" *ngFor="let reward of rewards">
          <div class="reward-image">
            <img [src]="reward.image" [alt]="reward.name">
                <div class="reward-badge" *ngIf="totalPoints >= reward.pointsRequired">
                  <i class="fas fa-check"></i>
                </div>
          </div>
          <div class="reward-info">
            <h3>{{ reward.name }}</h3>
            <p class="description">{{ reward.description }}</p>
                <div class="points-info">
                  <i class="fas fa-coins"></i>
                  <span class="points-required">{{ reward.pointsRequired }} points</span>
                </div>
          </div>
          <div class="reward-actions">
            <button class="btn-primary" 
                    [disabled]="totalPoints < reward.pointsRequired"
                    (click)="redeemReward(reward)">
                  <i class="fas fa-gift"></i>
                  {{ totalPoints >= reward.pointsRequired ? 'Redeem Now' : 'Not Enough Points' }}
            </button>
              </div>
          </div>
        </div>
      </div>
      
      <div class="earned-rewards">
        <h2>Recently Earned</h2>
          <div class="earned-list">
        <div class="earned-item" *ngFor="let earned of earnedRewards">
              <div class="earned-icon">
                <i class="fas fa-trophy"></i>
              </div>
          <div class="earned-info">
            <span class="reward-name">{{ earned.rewardName }}</span>
            <span class="earned-date">{{ earned.earnedDate }}</span>
          </div>
          <span class="points-earned">+{{ earned.points }} points</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .rewards-page {
      position: relative;
      min-height: 100vh;
    }
    
    .rewards-container { 
      padding: 2rem; 
      position: relative;
      z-index: 1;
    }
    
    .header { 
      display: flex; 
      justify-content: space-between; 
      align-items: center; 
      margin-bottom: 3rem; 
      flex-wrap: wrap;
      gap: 2rem;
    }
    
    .header h1 { 
      color: #1a1a1a;
      text-shadow: 0 1px 3px rgba(255, 255, 255, 0.8);
      font-size: 2.5rem;
      font-weight: 800;
    }
    
    .points-card {
      background: rgba(255, 255, 255, 0.95);
      border: 1px solid rgba(255, 255, 255, 0.3);
      border-radius: 1.5rem;
      padding: 1.5rem;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      backdrop-filter: blur(20px);
      display: flex;
      align-items: center;
      gap: 1rem;
      transition: all 0.3s ease;
    }
    
    .points-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .points-card i {
      color: var(--accent-color);
      font-size: 2rem;
    }
    
    .points-info {
      display: flex;
      flex-direction: column;
    }
    
    .points-label { 
      color: #2b2b2b; 
      font-size: 0.9rem;
      font-weight: 500;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .points-value { 
      color: var(--primary-color); 
      font-size: 2rem; 
      font-weight: 800;
      text-shadow: 0 2px 4px rgba(46, 139, 87, 0.3);
    }
    
    .rewards-section {
      margin-bottom: 3rem;
    }
    
    .rewards-section h2 {
      color: #1a1a1a;
      text-shadow: 0 1px 3px rgba(255, 255, 255, 0.8);
      font-size: 2rem;
      font-weight: 700;
      margin-bottom: 2rem;
    }
    
    .rewards-grid { 
      display: grid; 
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); 
      gap: 2rem; 
    }
    
    .reward-card { 
      background: rgba(255, 255, 255, 0.95); 
      border: 1px solid rgba(255, 255, 255, 0.3); 
      border-radius: 1.5rem; 
      padding: 2rem; 
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      backdrop-filter: blur(20px);
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }
    
    .reward-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .reward-image {
      position: relative;
      margin-bottom: 1.5rem;
    }
    
    .reward-image img { 
      width: 100%; 
      height: 200px; 
      object-fit: cover; 
      border-radius: 1rem; 
    }
    
    .reward-badge {
      position: absolute;
      top: 1rem;
      right: 1rem;
      background: var(--success-color);
      color: white;
      width: 30px;
      height: 30px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.8rem;
    }
    
    .reward-info h3 { 
      color: #1a1a1a; 
      margin-bottom: 0.75rem; 
      font-size: 1.5rem;
      font-weight: 700;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .description { 
      color: #2b2b2b; 
      margin-bottom: 1rem; 
      line-height: 1.5;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .points-info {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 1.5rem;
    }
    
    .points-info i {
      color: var(--accent-color);
      font-size: 1.1rem;
    }
    
    .points-required { 
      color: var(--accent-color); 
      font-weight: 700; 
      font-size: 1.1rem;
    }
    
    .reward-actions { 
      text-align: center; 
    }
    
    .btn-primary { 
      background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); 
      color: white; 
      border: none; 
      padding: 0.75rem 1.5rem; 
      border-radius: 0.75rem; 
      cursor: pointer; 
      width: 100%; 
      font-weight: 600;
      box-shadow: 0 4px 15px rgba(46, 139, 87, 0.3);
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
    }
    
    .btn-primary:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(46, 139, 87, 0.4);
    }
    
    .btn-primary:disabled { 
      background: rgba(0, 0, 0, 0.1); 
      color: rgba(0, 0, 0, 0.4); 
      cursor: not-allowed; 
      box-shadow: none;
    }
    
    .earned-rewards h2 { 
      color: #1a1a1a; 
      margin-bottom: 2rem; 
      font-size: 2rem;
      font-weight: 700;
      text-shadow: 0 1px 3px rgba(255, 255, 255, 0.8);
    }
    
    .earned-list {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    
    .earned-item { 
      display: flex; 
      align-items: center; 
      background: rgba(255, 255, 255, 0.95); 
      border: 1px solid rgba(255, 255, 255, 0.3); 
      border-radius: 1rem; 
      padding: 1.5rem; 
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      backdrop-filter: blur(20px);
      transition: all 0.3s ease;
      gap: 1rem;
    }
    
    .earned-item:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .earned-icon {
      width: 50px;
      height: 50px;
      background: linear-gradient(135deg, var(--accent-color), var(--primary-color));
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 1.2rem;
    }
    
    .earned-info { 
      display: flex; 
      flex-direction: column; 
      flex: 1;
    }
    
    .reward-name { 
      color: #1a1a1a; 
      font-weight: 700; 
      font-size: 1.1rem;
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .earned-date { 
      color: #2b2b2b; 
      font-size: 0.9rem; 
      text-shadow: 0 1px 2px rgba(255, 255, 255, 0.6);
    }
    
    .points-earned { 
      color: var(--success-color); 
      font-weight: 800; 
      font-size: 1.2rem;
      text-shadow: 0 2px 4px rgba(46, 139, 87, 0.3);
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
      .rewards-container {
        padding: 1rem;
      }
      
      .header {
        flex-direction: column;
        align-items: stretch;
        text-align: center;
      }
      
      .header h1 {
        font-size: 2rem;
        margin-bottom: 1rem;
      }
      
      .rewards-grid {
        grid-template-columns: 1fr;
        gap: 1.5rem;
      }
      
      .earned-item {
        flex-direction: column;
        text-align: center;
      }
    }
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