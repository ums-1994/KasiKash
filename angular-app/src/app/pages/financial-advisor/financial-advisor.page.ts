import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-financial-advisor',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  template: `
    <div class="financial-advisor-page">
      <!-- Header Section -->
      <div class="header-section mb-8">
        <h1 class="text-4xl font-bold text-gradient mb-4">Financial Advisor</h1>
        <p class="text-gray-300 text-lg">Get personalized financial guidance and investment strategies for your stokvel</p>
      </div>

      <!-- Quick Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="glass-card p-6 rounded-xl">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-2xl font-bold text-white">R 45,000</h3>
              <p class="text-gray-400">Total Portfolio Value</p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center">
              <i class="fas fa-chart-line text-white text-xl"></i>
            </div>
          </div>
        </div>

        <div class="glass-card p-6 rounded-xl">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-2xl font-bold text-white">12.5%</h3>
              <p class="text-gray-400">Annual Return</p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-purple-400 to-pink-500 rounded-full flex items-center justify-center">
              <i class="fas fa-percentage text-white text-xl"></i>
            </div>
          </div>
        </div>

        <div class="glass-card p-6 rounded-xl">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-2xl font-bold text-white">3</h3>
              <p class="text-gray-400">Active Investments</p>
            </div>
            <div class="w-12 h-12 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
              <i class="fas fa-coins text-white text-xl"></i>
            </div>
          </div>
        </div>
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Investment Recommendations -->
        <div class="glass-card p-6 rounded-xl">
          <h2 class="text-2xl font-bold text-white mb-6 flex items-center">
            <i class="fas fa-lightbulb mr-3 text-yellow-400"></i>
            Investment Recommendations
          </h2>
          
          <div class="space-y-4">
            <div class="recommendation-item p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <h4 class="text-lg font-semibold text-white mb-2">Government Bonds</h4>
                  <p class="text-gray-300 text-sm mb-3">Low-risk investment with guaranteed returns. Perfect for conservative stokvels.</p>
                  <div class="flex items-center text-sm">
                    <span class="text-green-400 font-semibold">Expected Return: 8.5%</span>
                    <span class="text-gray-400 mx-2">•</span>
                    <span class="text-gray-400">Risk: Low</span>
                  </div>
                </div>
                <button class="btn-primary px-4 py-2 text-sm">Invest</button>
              </div>
            </div>

            <div class="recommendation-item p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <h4 class="text-lg font-semibold text-white mb-2">Property Investment</h4>
                  <p class="text-gray-300 text-sm mb-3">Real estate investment for long-term wealth building and rental income.</p>
                  <div class="flex items-center text-sm">
                    <span class="text-green-400 font-semibold">Expected Return: 15.2%</span>
                    <span class="text-gray-400 mx-2">•</span>
                    <span class="text-yellow-400">Risk: Medium</span>
                  </div>
                </div>
                <button class="btn-primary px-4 py-2 text-sm">Learn More</button>
              </div>
            </div>

            <div class="recommendation-item p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <h4 class="text-lg font-semibold text-white mb-2">Stock Market ETF</h4>
                  <p class="text-gray-300 text-sm mb-3">Diversified exposure to South African equity markets through ETFs.</p>
                  <div class="flex items-center text-sm">
                    <span class="text-green-400 font-semibold">Expected Return: 12.8%</span>
                    <span class="text-gray-400 mx-2">•</span>
                    <span class="text-orange-400">Risk: Medium-High</span>
                  </div>
                </div>
                <button class="btn-primary px-4 py-2 text-sm">Invest</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Financial Planning Tools -->
        <div class="glass-card p-6 rounded-xl">
          <h2 class="text-2xl font-bold text-white mb-6 flex items-center">
            <i class="fas fa-calculator mr-3 text-blue-400"></i>
            Financial Planning Tools
          </h2>

          <div class="space-y-6">
            <!-- Goal Calculator -->
            <div class="tool-section">
              <h3 class="text-lg font-semibold text-white mb-4">Savings Goal Calculator</h3>
              <div class="space-y-4">
                <div>
                  <label class="block text-gray-300 text-sm mb-2">Target Amount (R)</label>
                  <input type="number" class="input-field w-full" placeholder="100000" [(ngModel)]="targetAmount">
                </div>
                <div>
                  <label class="block text-gray-300 text-sm mb-2">Time Period (Years)</label>
                  <input type="number" class="input-field w-full" placeholder="5" [(ngModel)]="timePeriod">
                </div>
                <button class="btn-primary w-full" (click)="calculateSavings()">Calculate</button>
                <div *ngIf="monthlyContribution" class="result-box p-4 bg-green-900 bg-opacity-30 rounded-lg border border-green-500">
                  <p class="text-green-300 text-sm">Monthly contribution needed:</p>
                  <p class="text-2xl font-bold text-green-400">R {{ monthlyContribution | number:'1.2-2' }}</p>
                </div>
              </div>
            </div>

            <!-- Risk Assessment -->
            <div class="tool-section">
              <h3 class="text-lg font-semibold text-white mb-4">Risk Assessment</h3>
              <div class="space-y-3">
                <div class="risk-option p-3 bg-gray-800 bg-opacity-50 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors" 
                     [class.selected]="selectedRisk === 'conservative'" 
                     (click)="selectRisk('conservative')">
                  <div class="flex items-center justify-between">
                    <div>
                      <h4 class="text-white font-medium">Conservative</h4>
                      <p class="text-gray-400 text-sm">Low risk, stable returns</p>
                    </div>
                    <div class="w-4 h-4 rounded-full border-2" [class.bg-blue-500]="selectedRisk === 'conservative'"></div>
                  </div>
                </div>

                <div class="risk-option p-3 bg-gray-800 bg-opacity-50 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors"
                     [class.selected]="selectedRisk === 'moderate'" 
                     (click)="selectRisk('moderate')">
                  <div class="flex items-center justify-between">
                    <div>
                      <h4 class="text-white font-medium">Moderate</h4>
                      <p class="text-gray-400 text-sm">Balanced risk and return</p>
                    </div>
                    <div class="w-4 h-4 rounded-full border-2" [class.bg-blue-500]="selectedRisk === 'moderate'"></div>
                  </div>
                </div>

                <div class="risk-option p-3 bg-gray-800 bg-opacity-50 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors"
                     [class.selected]="selectedRisk === 'aggressive'" 
                     (click)="selectRisk('aggressive')">
                  <div class="flex items-center justify-between">
                    <div>
                      <h4 class="text-white font-medium">Aggressive</h4>
                      <p class="text-gray-400 text-sm">High risk, high potential returns</p>
                    </div>
                    <div class="w-4 h-4 rounded-full border-2" [class.bg-blue-500]="selectedRisk === 'aggressive'"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Chat with Advisor Section -->
      <div class="glass-card p-6 rounded-xl mt-8">
        <h2 class="text-2xl font-bold text-white mb-6 flex items-center">
          <i class="fas fa-comments mr-3 text-purple-400"></i>
          Chat with Your Financial Advisor
        </h2>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 class="text-lg font-semibold text-white mb-4">Available Advisors</h3>
            <div class="space-y-3">
              <div class="advisor-card p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
                <div class="flex items-center">
                  <div class="w-12 h-12 bg-gradient-to-r from-blue-400 to-purple-500 rounded-full flex items-center justify-center mr-4">
                    <span class="text-white font-bold">SM</span>
                  </div>
                  <div class="flex-1">
                    <h4 class="text-white font-medium">Sarah Mthembu</h4>
                    <p class="text-gray-400 text-sm">Senior Financial Advisor</p>
                    <p class="text-green-400 text-xs">Online</p>
                  </div>
                  <button class="btn-primary px-3 py-1 text-sm">Chat</button>
                </div>
              </div>

              <div class="advisor-card p-4 bg-gray-800 bg-opacity-50 rounded-lg border border-gray-700">
                <div class="flex items-center">
                  <div class="w-12 h-12 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center mr-4">
                    <span class="text-white font-bold">TK</span>
                  </div>
                  <div class="flex-1">
                    <h4 class="text-white font-medium">Thabo Khumalo</h4>
                    <p class="text-gray-400 text-sm">Investment Specialist</p>
                    <p class="text-yellow-400 text-xs">Away</p>
                  </div>
                  <button class="btn-secondary px-3 py-1 text-sm">Schedule</button>
                </div>
              </div>
            </div>
          </div>

          <div>
            <h3 class="text-lg font-semibold text-white mb-4">Quick Questions</h3>
            <div class="space-y-2">
              <button class="quick-question-btn w-full text-left p-3 bg-gray-800 bg-opacity-50 rounded-lg hover:bg-gray-700 transition-colors">
                <i class="fas fa-question-circle mr-2 text-blue-400"></i>
                How should I diversify my stokvel investments?
              </button>
              <button class="quick-question-btn w-full text-left p-3 bg-gray-800 bg-opacity-50 rounded-lg hover:bg-gray-700 transition-colors">
                <i class="fas fa-question-circle mr-2 text-blue-400"></i>
                What's the best time to invest in property?
              </button>
              <button class="quick-question-btn w-full text-left p-3 bg-gray-800 bg-opacity-50 rounded-lg hover:bg-gray-700 transition-colors">
                <i class="fas fa-question-circle mr-2 text-blue-400"></i>
                How do I minimize investment risks?
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .financial-advisor-page {
      padding: 2rem;
      min-height: 100vh;
    }

    .glass-card {
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }

    .text-gradient {
      background: linear-gradient(90deg, #7B61FF, #61DAFB);
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .input-field {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: white;
      padding: 0.75rem 1rem;
      border-radius: 0.5rem;
      transition: all 0.3s ease;
    }

    .input-field:focus {
      outline: none;
      border-color: #7B61FF;
      box-shadow: 0 0 0 2px rgba(123, 97, 255, 0.2);
    }

    .input-field::placeholder {
      color: rgba(255, 255, 255, 0.5);
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

    .quick-question-btn {
      color: rgba(255, 255, 255, 0.8);
      transition: all 0.3s ease;
    }

    .quick-question-btn:hover {
      color: white;
    }

    .risk-option.selected {
      border-color: #7B61FF;
      background: rgba(123, 97, 255, 0.1);
    }

    .result-box {
      animation: slideIn 0.3s ease;
    }

    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateY(-10px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `]
})
export class FinancialAdvisorPage {
  targetAmount: number = 0;
  timePeriod: number = 0;
  monthlyContribution: number = 0;
  selectedRisk: string = 'moderate';

  calculateSavings() {
    if (this.targetAmount && this.timePeriod) {
      // Simple calculation: target amount / (time period * 12 months)
      this.monthlyContribution = this.targetAmount / (this.timePeriod * 12);
    }
  }

  selectRisk(risk: string) {
    this.selectedRisk = risk;
  }
}
