import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-savings-goals',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  template: `
    <div class="savings-goals-page">
      <!-- Header Section -->
      <div class="header-section mb-8">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-4xl font-bold text-gradient mb-4">Savings Goals</h1>
            <p class="text-gray-300 text-lg">Set and track your financial goals to achieve your dreams</p>
          </div>
          <button class="btn-primary" (click)="showCreateGoalModal = true">
            <i class="fas fa-plus mr-2"></i>
            Create New Goal
          </button>
        </div>
      </div>

      <!-- Progress Overview -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="glass-card p-6 rounded-xl">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-2xl font-bold text-white">{{ totalGoals }}</h3>
              <p class="text-gray-400">Total Goals</p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-blue-400 to-purple-500 rounded-full flex items-center justify-center">
              <i class="fas fa-bullseye text-white text-xl"></i>
            </div>
          </div>
        </div>

        <div class="glass-card p-6 rounded-xl">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-2xl font-bold text-white">{{ completedGoals }}</h3>
              <p class="text-gray-400">Completed</p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center">
              <i class="fas fa-check-circle text-white text-xl"></i>
            </div>
          </div>
        </div>

        <div class="glass-card p-6 rounded-xl">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-2xl font-bold text-white">R {{ totalSaved | number:'1.0-0' }}</h3>
              <p class="text-gray-400">Total Saved</p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
              <i class="fas fa-piggy-bank text-white text-xl"></i>
            </div>
          </div>
        </div>

        <div class="glass-card p-6 rounded-xl">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-2xl font-bold text-white">{{ averageProgress }}%</h3>
              <p class="text-gray-400">Avg Progress</p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-purple-400 to-pink-500 rounded-full flex items-center justify-center">
              <i class="fas fa-chart-line text-white text-xl"></i>
            </div>
          </div>
        </div>
      </div>

      <!-- Goals Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        <div *ngFor="let goal of savingsGoals" class="glass-card p-6 rounded-xl goal-card">
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
              <h3 class="text-xl font-bold text-white mb-2">{{ goal.title }}</h3>
              <p class="text-gray-400 text-sm mb-3">{{ goal.description }}</p>
              <div class="flex items-center text-sm text-gray-300">
                <i class="fas fa-calendar mr-2"></i>
                <span>Target: {{ goal.targetDate | date:'MMM yyyy' }}</span>
              </div>
            </div>
            <div class="goal-icon w-12 h-12 rounded-full flex items-center justify-center" [style.background]="goal.iconBg">
              <i [class]="goal.icon + ' text-white text-xl'"></i>
            </div>
          </div>

          <!-- Progress Bar -->
          <div class="mb-4">
            <div class="flex justify-between text-sm mb-2">
              <span class="text-gray-300">Progress</span>
              <span class="text-white font-semibold">{{ goal.progress }}%</span>
            </div>
            <div class="progress-bar-bg">
              <div class="progress-bar" [style.width.%]="goal.progress" [style.background]="goal.progressColor"></div>
            </div>
          </div>

          <!-- Amount Info -->
          <div class="flex justify-between items-center mb-4">
            <div>
              <p class="text-gray-400 text-sm">Saved</p>
              <p class="text-white font-bold">R {{ goal.savedAmount | number:'1.0-0' }}</p>
            </div>
            <div class="text-right">
              <p class="text-gray-400 text-sm">Target</p>
              <p class="text-white font-bold">R {{ goal.targetAmount | number:'1.0-0' }}</p>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex space-x-2">
            <button class="btn-primary flex-1 text-sm" (click)="addContribution(goal)">
              <i class="fas fa-plus mr-1"></i>
              Add Money
            </button>
            <button class="btn-secondary text-sm px-3" (click)="editGoal(goal)">
              <i class="fas fa-edit"></i>
            </button>
            <button class="btn-danger text-sm px-3" (click)="deleteGoal(goal)">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- Create Goal Modal -->
      <div *ngIf="showCreateGoalModal" class="modal-overlay" (click)="closeModal()">
        <div class="modal-content" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <h2 class="text-2xl font-bold text-white">Create New Savings Goal</h2>
            <button class="close-btn" (click)="closeModal()">
              <i class="fas fa-times"></i>
            </button>
          </div>

          <form (ngSubmit)="createGoal()" class="modal-body">
            <div class="form-group">
              <label class="form-label">Goal Title</label>
              <input type="text" class="form-input" [(ngModel)]="newGoal.title" name="title" required>
            </div>

            <div class="form-group">
              <label class="form-label">Description</label>
              <textarea class="form-input" rows="3" [(ngModel)]="newGoal.description" name="description"></textarea>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="form-group">
                <label class="form-label">Target Amount (R)</label>
                <input type="number" class="form-input" [(ngModel)]="newGoal.targetAmount" name="targetAmount" required>
              </div>

              <div class="form-group">
                <label class="form-label">Target Date</label>
                <input type="date" class="form-input" [(ngModel)]="newGoal.targetDate" name="targetDate" required>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">Goal Category</label>
              <select class="form-input" [(ngModel)]="newGoal.category" name="category">
                <option value="house">House</option>
                <option value="car">Car</option>
                <option value="education">Education</option>
                <option value="vacation">Vacation</option>
                <option value="emergency">Emergency Fund</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-secondary" (click)="closeModal()">Cancel</button>
              <button type="submit" class="btn-primary">Create Goal</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .savings-goals-page {
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
      transform: translateY(-5px);
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

    .btn-danger {
      background: rgba(239, 68, 68, 0.1);
      color: #ef4444;
      border: 1px solid rgba(239, 68, 68, 0.2);
      padding: 0.5rem 1rem;
      border-radius: 0.5rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .btn-danger:hover {
      background: rgba(239, 68, 68, 0.2);
    }

    .progress-bar-bg {
      width: 100%;
      height: 8px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 4px;
      overflow: hidden;
    }

    .progress-bar {
      height: 100%;
      border-radius: 4px;
      transition: width 0.3s ease;
    }

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
    }

    .modal-content {
      background: rgba(30, 41, 59, 0.95);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 1rem;
      width: 90%;
      max-width: 500px;
      max-height: 90vh;
      overflow-y: auto;
    }

    .modal-header {
      display: flex;
      justify-content: between;
      align-items: center;
      padding: 1.5rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .close-btn {
      background: none;
      border: none;
      color: rgba(255, 255, 255, 0.6);
      font-size: 1.5rem;
      cursor: pointer;
      padding: 0.5rem;
      border-radius: 0.5rem;
      transition: all 0.3s ease;
    }

    .close-btn:hover {
      color: white;
      background: rgba(255, 255, 255, 0.1);
    }

    .modal-body {
      padding: 1.5rem;
    }

    .form-group {
      margin-bottom: 1.5rem;
    }

    .form-label {
      display: block;
      color: rgba(255, 255, 255, 0.8);
      font-weight: 500;
      margin-bottom: 0.5rem;
    }

    .form-input {
      width: 100%;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: white;
      padding: 0.75rem 1rem;
      border-radius: 0.5rem;
      transition: all 0.3s ease;
    }

    .form-input:focus {
      outline: none;
      border-color: #7B61FF;
      box-shadow: 0 0 0 2px rgba(123, 97, 255, 0.2);
    }

    .form-input::placeholder {
      color: rgba(255, 255, 255, 0.5);
    }

    .modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: 1rem;
      padding: 1.5rem;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
    }
  `]
})
export class SavingsGoalsPage {
  showCreateGoalModal = false;
  
  newGoal = {
    title: '',
    description: '',
    targetAmount: 0,
    targetDate: '',
    category: 'other'
  };

  savingsGoals = [
    {
      id: 1,
      title: 'New House',
      description: 'Save for a down payment on our dream home',
      targetAmount: 500000,
      savedAmount: 125000,
      targetDate: '2025-12-31',
      progress: 25,
      category: 'house',
      icon: 'fas fa-home',
      iconBg: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
      progressColor: 'linear-gradient(90deg, #3b82f6, #1d4ed8)'
    },
    {
      id: 2,
      title: 'Emergency Fund',
      description: 'Build a 6-month emergency fund for unexpected expenses',
      targetAmount: 100000,
      savedAmount: 75000,
      targetDate: '2024-06-30',
      progress: 75,
      category: 'emergency',
      icon: 'fas fa-shield-alt',
      iconBg: 'linear-gradient(135deg, #10b981, #059669)',
      progressColor: 'linear-gradient(90deg, #10b981, #059669)'
    },
    {
      id: 3,
      title: 'Family Vacation',
      description: 'Trip to Cape Town for the whole family',
      targetAmount: 25000,
      savedAmount: 15000,
      targetDate: '2024-03-15',
      progress: 60,
      category: 'vacation',
      icon: 'fas fa-plane',
      iconBg: 'linear-gradient(135deg, #f59e0b, #d97706)',
      progressColor: 'linear-gradient(90deg, #f59e0b, #d97706)'
    },
    {
      id: 4,
      title: 'New Car',
      description: 'Replace our old car with a reliable family vehicle',
      targetAmount: 300000,
      savedAmount: 45000,
      targetDate: '2025-08-31',
      progress: 15,
      category: 'car',
      icon: 'fas fa-car',
      iconBg: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
      progressColor: 'linear-gradient(90deg, #8b5cf6, #7c3aed)'
    }
  ];

  get totalGoals(): number {
    return this.savingsGoals.length;
  }

  get completedGoals(): number {
    return this.savingsGoals.filter(goal => goal.progress >= 100).length;
  }

  get totalSaved(): number {
    return this.savingsGoals.reduce((total, goal) => total + goal.savedAmount, 0);
  }

  get averageProgress(): number {
    const totalProgress = this.savingsGoals.reduce((total, goal) => total + goal.progress, 0);
    return Math.round(totalProgress / this.savingsGoals.length);
  }

  createGoal() {
    const goal = {
      id: Date.now(),
      ...this.newGoal,
      savedAmount: 0,
      progress: 0,
      icon: this.getIconForCategory(this.newGoal.category),
      iconBg: this.getIconBgForCategory(this.newGoal.category),
      progressColor: this.getProgressColorForCategory(this.newGoal.category)
    };
    
    this.savingsGoals.push(goal);
    this.closeModal();
    this.resetNewGoal();
  }

  closeModal() {
    this.showCreateGoalModal = false;
  }

  resetNewGoal() {
    this.newGoal = {
      title: '',
      description: '',
      targetAmount: 0,
      targetDate: '',
      category: 'other'
    };
  }

  addContribution(goal: any) {
    const amount = prompt('Enter contribution amount:');
    if (amount && !isNaN(Number(amount))) {
      goal.savedAmount += Number(amount);
      goal.progress = Math.min(100, Math.round((goal.savedAmount / goal.targetAmount) * 100));
    }
  }

  editGoal(goal: any) {
    // Implementation for editing goal
    console.log('Edit goal:', goal);
  }

  deleteGoal(goal: any) {
    if (confirm('Are you sure you want to delete this goal?')) {
      const index = this.savingsGoals.findIndex(g => g.id === goal.id);
      if (index > -1) {
        this.savingsGoals.splice(index, 1);
      }
    }
  }

  private getIconForCategory(category: string): string {
    const icons: { [key: string]: string } = {
      house: 'fas fa-home',
      car: 'fas fa-car',
      education: 'fas fa-graduation-cap',
      vacation: 'fas fa-plane',
      emergency: 'fas fa-shield-alt',
      other: 'fas fa-bullseye'
    };
    return icons[category] || 'fas fa-bullseye';
  }

  private getIconBgForCategory(category: string): string {
    const backgrounds: { [key: string]: string } = {
      house: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
      car: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
      education: 'linear-gradient(135deg, #06b6d4, #0891b2)',
      vacation: 'linear-gradient(135deg, #f59e0b, #d97706)',
      emergency: 'linear-gradient(135deg, #10b981, #059669)',
      other: 'linear-gradient(135deg, #6b7280, #4b5563)'
    };
    return backgrounds[category] || 'linear-gradient(135deg, #6b7280, #4b5563)';
  }

  private getProgressColorForCategory(category: string): string {
    const colors: { [key: string]: string } = {
      house: 'linear-gradient(90deg, #3b82f6, #1d4ed8)',
      car: 'linear-gradient(90deg, #8b5cf6, #7c3aed)',
      education: 'linear-gradient(90deg, #06b6d4, #0891b2)',
      vacation: 'linear-gradient(90deg, #f59e0b, #d97706)',
      emergency: 'linear-gradient(90deg, #10b981, #059669)',
      other: 'linear-gradient(90deg, #6b7280, #4b5563)'
    };
    return colors[category] || 'linear-gradient(90deg, #6b7280, #4b5563)';
  }
}
