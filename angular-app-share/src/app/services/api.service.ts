import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { delay } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  
  // Local storage keys
  private readonly STORAGE_KEYS = {
    user: 'kk_user',
    settings: 'kk_settings',
    stokvels: 'kk_stokvels',
    contributions: 'kk_contributions',
    notifications: 'kk_notifications',
    points: 'kk_points',
    earnedRewards: 'kk_earned_rewards',
    activities: 'kk_activities',
    cart: 'kk_cart'
  } as const;

  // Utility: safe localStorage access (SSR friendly)
  private get storage(): Storage | null {
    try {
      return typeof window !== 'undefined' ? window.localStorage : null;
    } catch {
      return null;
    }
  }

  private read<T>(key: string, fallback: T): T {
    const store = this.storage;
    if (!store) return fallback;
    const raw = store.getItem(key);
    if (!raw) return fallback;
    try { return JSON.parse(raw) as T; } catch { return fallback; }
  }

  private write<T>(key: string, value: T): void {
    const store = this.storage;
    if (!store) return;
    store.setItem(key, JSON.stringify(value));
  }

  // Admin dashboard stats (requires session auth)
  getAdminStats(): Observable<any> {
    // Temporarily return mock data until Flask is running
    return of({
      total_users: 150,
      total_members: 89,
      pending_loans: 12,
      kyc_pending: 23,
      total_deposits: 45000.5,
      new_notifications: this.getNotifications().length,
      members_change: 12.5,
      deposits_change: 8.3,
      timestamp: new Date().toISOString(),
      note: 'Mock data - Flask backend not running'
    }).pipe(delay(400));
  }

  // Auth
  getCurrentUser() {
    return this.read(this.STORAGE_KEYS.user, {
      name: 'John Doe',
      email: 'john.doe@example.com',
      avatar: 'assets/default-avatar.png'
    });
  }

  setCurrentUser(user: any): void {
    this.write(this.STORAGE_KEYS.user, user);
  }

  logout(): void {
    if (!this.storage) return;
    this.storage.removeItem(this.STORAGE_KEYS.user);
  }

  // Settings
  getSettings() {
    return this.read(this.STORAGE_KEYS.settings, {
      emailNotifications: true,
      smsNotifications: false,
      twoFactorAuth: true,
      profileVisibility: 'members',
      showContributionHistory: true,
      language: 'en',
      currency: 'ZAR'
    });
  }

  saveSettings(settings: any): void {
    this.write(this.STORAGE_KEYS.settings, settings);
  }

  resetSettings(): any {
    const defaults = {
      emailNotifications: true,
      smsNotifications: false,
      twoFactorAuth: true,
      profileVisibility: 'members',
      showContributionHistory: true,
      language: 'en',
      currency: 'ZAR'
    };
    this.write(this.STORAGE_KEYS.settings, defaults);
    return defaults;
  }

  // Stokvels
  getStokvels() {
    return this.read(this.STORAGE_KEYS.stokvels, [
      { id: '1', name: 'Family Savings', status: 'active', memberCount: 12, monthlyContribution: 500, totalFund: 15000, role: 'admin', isCreator: true },
      { id: '2', name: 'Business Investment', status: 'active', memberCount: 8, monthlyContribution: 1000, totalFund: 25000, role: 'member', isCreator: false }
    ]);
  }

  createStokvel(stokvel: { name: string; description?: string; contributionAmount: number; meetingDay?: string }): any {
    const stokvels = this.getStokvels();
    const newEntry = {
      id: (Date.now()).toString(),
      name: stokvel.name,
      status: 'active',
      memberCount: 1,
      monthlyContribution: stokvel.contributionAmount,
      totalFund: 0,
      role: 'admin',
      isCreator: true
    };
    stokvels.unshift(newEntry);
    this.write(this.STORAGE_KEYS.stokvels, stokvels);
    // Log activity
    this.addActivity({
      type: 'stokvel',
      title: 'New Stokvel Created',
      description: `Created "${newEntry.name}" stokvel`,
      time: 'Just now'
    });
    return newEntry;
  }

  deleteStokvel(stokvelId: string): { success: boolean; message: string } {
    const stokvels = this.getStokvels();
    const stokvelIndex = stokvels.findIndex(s => s.id === stokvelId);
    
    if (stokvelIndex === -1) {
      return { success: false, message: 'Stokvel not found' };
    }

    const stokvelToDelete = stokvels[stokvelIndex];
    stokvels.splice(stokvelIndex, 1);
    this.write(this.STORAGE_KEYS.stokvels, stokvels);

    // Log activity
    this.addActivity({
      type: 'stokvel',
      title: 'Stokvel Deleted',
      description: `Deleted "${stokvelToDelete.name}" stokvel`,
      time: 'Just now'
    });

    // TODO: When Flask backend is running, uncomment this to integrate with backend
    // this.deleteStokvelFromBackend(stokvelId).subscribe({
    //   next: (response) => console.log('Backend delete successful:', response),
    //   error: (error) => console.error('Backend delete failed:', error)
    // });

    return { success: true, message: `Successfully deleted "${stokvelToDelete.name}" stokvel` };
  }

  // Backend integration method (for when Flask is running)
  private deleteStokvelFromBackend(stokvelId: string): Observable<any> {
    return this.http.post(`/stokvel/${stokvelId}/delete`, {}, {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  leaveStokvel(stokvelId: string): { success: boolean; message: string } {
    const stokvels = this.getStokvels();
    const stokvelIndex = stokvels.findIndex(s => s.id === stokvelId);
    
    if (stokvelIndex === -1) {
      return { success: false, message: 'Stokvel not found' };
    }

    const stokvelToLeave = stokvels[stokvelIndex];
    stokvels.splice(stokvelIndex, 1);
    this.write(this.STORAGE_KEYS.stokvels, stokvels);

    // Log activity
    this.addActivity({
      type: 'stokvel',
      title: 'Left Stokvel',
      description: `Left "${stokvelToLeave.name}" stokvel`,
      time: 'Just now'
    });

    return { success: true, message: `Successfully left "${stokvelToLeave.name}" stokvel` };
  }

  // Contributions
  getContributions() {
    return this.read(this.STORAGE_KEYS.contributions, [
      { id: 'c1', stokvelName: 'Family Savings', amount: 500, date: '01 Dec 2024', status: 'completed' },
      { id: 'c2', stokvelName: 'Business Investment', amount: 1000, date: '30 Nov 2024', status: 'completed' }
    ]);
  }

  addContribution(payload: { stokvelId: string; amount: number; method: string }): any {
    const stokvels = this.getStokvels();
    const stokvel = stokvels.find(s => s.id === payload.stokvelId);
    const contributions = this.getContributions();
    const contribution = {
      id: 'c' + Date.now().toString(),
      stokvelName: stokvel?.name || 'Unknown',
      amount: payload.amount,
      date: new Date().toLocaleDateString('en-ZA'),
      status: 'completed'
    };
    contributions.unshift(contribution);
    this.write(this.STORAGE_KEYS.contributions, contributions);
    if (stokvel) {
      stokvel.totalFund += payload.amount;
      this.write(this.STORAGE_KEYS.stokvels, stokvels);
    }
    // Log activity
    this.addActivity({
      type: 'contribution',
      title: 'Contribution Made',
      description: `R${payload.amount} contributed to ${contribution.stokvelName}`,
      time: 'Just now',
      amount: payload.amount
    });
    return contribution;
  }

  // Activities
  getActivities(): any[] {
    return this.read(this.STORAGE_KEYS.activities, [
      { type: 'contribution', title: 'Contribution Made', description: 'R500 contributed to Family Savings stokvel', time: '2 hours ago', amount: 500 },
      { type: 'stokvel', title: 'New Member Joined', description: 'Sarah Johnson joined Family Savings stokvel', time: '1 day ago' },
      { type: 'reward', title: 'Points Earned', description: 'Earned 100 points for monthly contribution', time: '2 days ago', amount: 100 },
      { type: 'payout', title: 'Payout Requested', description: 'R2000 payout requested from Business Investment', time: '3 days ago', amount: 2000 }
    ]);
  }

  addActivity(entry: { type: string; title: string; description: string; time: string; amount?: number }): void {
    const list = this.getActivities();
    list.unshift(entry);
    this.write(this.STORAGE_KEYS.activities, list);
  }

  // Notifications
  getNotifications(): any[] {
    return this.read(this.STORAGE_KEYS.notifications, [
      { id: 1, title: 'Contribution Received', message: 'Your contribution of R500 has been received for Family Savings stokvel', type: 'success', time: '2 hours ago', isRead: false },
      { id: 2, title: 'KYC Approved', message: 'Congratulations! Your KYC verification has been approved', type: 'info', time: '1 day ago', isRead: false },
      { id: 3, title: 'New Member Joined', message: 'Sarah Johnson has joined your Family Savings stokvel', type: 'info', time: '2 days ago', isRead: true },
      { id: 4, title: 'Payout Available', message: 'You have R2000 available for payout from Business Investment stokvel', type: 'warning', time: '3 days ago', isRead: true }
    ]);
  }

  setNotifications(notifications: any[]): void {
    this.write(this.STORAGE_KEYS.notifications, notifications);
  }

  markAllNotificationsRead(): void {
    const list = this.getNotifications().map(n => ({ ...n, isRead: true }));
    this.write(this.STORAGE_KEYS.notifications, list);
  }

  markNotificationRead(id: number): void {
    const list = this.getNotifications().map(n => n.id === id ? { ...n, isRead: true } : n);
    this.write(this.STORAGE_KEYS.notifications, list);
  }

  deleteNotification(id: number): void {
    const list = this.getNotifications().filter(n => n.id !== id);
    this.write(this.STORAGE_KEYS.notifications, list);
  }

  // Rewards
  getRewardsCatalog() {
    return [
      { id: 1, name: 'R50 Voucher', description: 'Get R50 off your next purchase', pointsRequired: 500, image: 'assets/voucher.jpg' },
      { id: 2, name: 'Free Contribution', description: 'Skip one month contribution', pointsRequired: 1000, image: 'assets/contribution.jpg' },
      { id: 3, name: 'Premium Support', description: 'Priority customer support for 30 days', pointsRequired: 2000, image: 'assets/support.jpg' }
    ];
  }

  getPoints(): number {
    return this.read(this.STORAGE_KEYS.points, 1250);
  }

  setPoints(points: number): void {
    this.write(this.STORAGE_KEYS.points, points);
  }

  getEarnedRewards(): any[] {
    return this.read(this.STORAGE_KEYS.earnedRewards, [
      { rewardName: 'Monthly Contribution', earnedDate: '01 Dec 2024', points: 100 },
      { rewardName: 'Referral Bonus', earnedDate: '28 Nov 2024', points: 250 }
    ]);
  }

  setEarnedRewards(list: any[]): void {
    this.write(this.STORAGE_KEYS.earnedRewards, list);
  }

  redeemReward(rewardId: number): { success: boolean; message: string; points: number } {
    const catalog = this.getRewardsCatalog();
    const reward = catalog.find(r => r.id === rewardId);
    if (!reward) return { success: false, message: 'Reward not found', points: this.getPoints() };
    const current = this.getPoints();
    if (current < reward.pointsRequired) {
      return { success: false, message: 'Not enough points', points: current };
    }
    const updated = current - reward.pointsRequired;
    this.setPoints(updated);
    const earned = this.getEarnedRewards();
    earned.unshift({ rewardName: reward.name, earnedDate: new Date().toLocaleDateString('en-ZA'), points: -reward.pointsRequired });
    this.setEarnedRewards(earned);
    return { success: true, message: `Redeemed ${reward.name}`, points: updated };
  }

  // Marketplace
  getProducts() {
    return [
      { id: 1, name: 'Smartphone', description: 'Latest smartphone with great features', price: 2500, seller: 'TechStore', image: 'assets/phone.jpg', category: 'electronics' },
      { id: 2, name: 'T-Shirt', description: 'Comfortable cotton t-shirt', price: 150, seller: 'FashionHub', image: 'assets/tshirt.jpg', category: 'clothing' }
    ];
  }

  getCart(): any[] {
    return this.read(this.STORAGE_KEYS.cart, [] as any[]);
  }

  addToCart(productId: number): void {
    const cart = this.getCart();
    const existing = cart.find(c => c.productId === productId);
    if (existing) existing.quantity += 1; else cart.push({ productId, quantity: 1 });
    this.write(this.STORAGE_KEYS.cart, cart);
  }

  checkout(): { success: boolean; message: string } {
    this.write(this.STORAGE_KEYS.cart, []);
    return { success: true, message: 'Checkout complete' };
  }
}

