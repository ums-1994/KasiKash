import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-notifications',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="notifications-container">
      <div class="header">
        <h1>Notifications</h1>
        <button class="btn-secondary" (click)="markAllAsRead()">Mark All as Read</button>
      </div>
      
      <div class="notifications-list">
        <div class="notification-item" 
             *ngFor="let notification of notifications"
             [class.unread]="!notification.isRead"
             (click)="markAsRead(notification)">
          <div class="notification-icon" [class]="notification.type">
            <i [class]="getIconClass(notification.type)"></i>
          </div>
          <div class="notification-content">
            <h4>{{ notification.title }}</h4>
            <p>{{ notification.message }}</p>
            <span class="notification-time">{{ notification.time }}</span>
          </div>
          <div class="notification-actions">
            <button class="btn-small" (click)="deleteNotification(notification)">Delete</button>
          </div>
        </div>
      </div>
      
      <div class="no-notifications" *ngIf="notifications.length === 0">
        <p>No notifications to display</p>
      </div>
    </div>
  `,
  styles: [`
    .notifications-container { padding: 2rem; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
    .header h1 { color: #fff; }
    .btn-secondary { background: rgba(255,255,255,0.1); color: #fff; border: 1px solid rgba(255,255,255,0.2); padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; }
    .notifications-list { display: flex; flex-direction: column; gap: 1rem; }
    .notification-item { display: flex; align-items: center; gap: 1rem; padding: 1rem; background: rgba(255,255,255,0.03); border-radius: 0.5rem; cursor: pointer; transition: all 0.3s ease; }
    .notification-item:hover { background: rgba(255,255,255,0.05); }
    .notification-item.unread { border-left: 4px solid var(--primary-color); background: rgba(85,99,222,0.08); }
    .notification-icon { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; }
    .notification-icon.success { background: rgba(76,175,80,0.2); color: #4CAF50; }
    .notification-icon.info { background: rgba(33,150,243,0.2); color: #2196F3; }
    .notification-icon.warning { background: rgba(255,152,0,0.2); color: #FF9800; }
    .notification-icon.error { background: rgba(244,67,54,0.2); color: #F44336; }
    .notification-content { flex: 1; }
    .notification-content h4 { color: #fff; font-weight: 600; margin-bottom: 0.25rem; }
    .notification-content p { color: rgba(255,255,255,0.7); font-size: 0.875rem; margin-bottom: 0.25rem; }
    .notification-time { font-size: 0.75rem; color: rgba(255,255,255,0.5); }
    .notification-actions { display: flex; gap: 0.5rem; }
    .btn-small { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.8); border: 1px solid rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 0.375rem; font-size: 0.875rem; cursor: pointer; }
    .btn-small:hover { background: rgba(255,255,255,0.15); color: #fff; }
    .no-notifications { text-align: center; padding: 2rem; color: rgba(255,255,255,0.6); }
  `]
})
export class NotificationsPage {
  notifications: any[] = [];

  constructor(private api: ApiService) {
    this.notifications = this.api.getNotifications();
  }
  
  getIconClass(type: string): string {
    const iconMap: { [key: string]: string } = {
      success: 'fas fa-check-circle',
      info: 'fas fa-info-circle',
      warning: 'fas fa-exclamation-triangle',
      error: 'fas fa-times-circle'
    };
    return iconMap[type] || 'fas fa-bell';
  }
  
  markAsRead(notification: any) {
    this.api.markNotificationRead(notification.id);
    this.notifications = this.api.getNotifications();
  }
  
  markAllAsRead() {
    this.api.markAllNotificationsRead();
    this.notifications = this.api.getNotifications();
  }
  
  deleteNotification(notification: any) {
    this.api.deleteNotification(notification.id);
    this.notifications = this.api.getNotifications();
  }
} 