import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <section style="max-width:360px;margin:40px auto;padding:16px;border:1px solid #eee;border-radius:8px;">
      <h2>Login (placeholder)</h2>
      <p>This is a placeholder for your auth integration.</p>
      <form (submit)="onSubmit($event)">
        <label>Email</label>
        <input type="email" class="form-control" [(ngModel)]="email" name="email" />
        <label>Password</label>
        <input type="password" class="form-control" [(ngModel)]="password" name="password" />
        <button type="submit">Login</button>
      </form>
    </section>
  `
})
export class LoginPage {
  email = '';
  password = '';

  constructor(private api: ApiService, private router: Router) {}

  onSubmit(e: Event) {
    e.preventDefault();
    // Mock login: set current user and redirect
    this.api.setCurrentUser({ name: 'John Doe', email: this.email || 'john.doe@example.com', avatar: 'assets/default-avatar.png' });
    this.router.navigate(['/dashboard']);
  }
}

