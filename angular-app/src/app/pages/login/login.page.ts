import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <section style="max-width:360px;margin:40px auto;padding:16px;border:1px solid #eee;border-radius:8px;">
      <h2>Login (placeholder)</h2>
      <p>This is a placeholder for your auth integration.</p>
      <form (submit)="$event.preventDefault()">
        <label>Email</label>
        <input type="email" class="form-control" />
        <label>Password</label>
        <input type="password" class="form-control" />
        <button type="submit">Login</button>
      </form>
    </section>
  `
})
export class LoginPage {}

