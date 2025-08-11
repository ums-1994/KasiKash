import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <section style="padding:16px">
      <h2>Dashboard</h2>
      <pre *ngIf="stats() as s">{{ s | json }}</pre>
      <p *ngIf="!stats()">Loading...</p>
    </section>
  `
})
export class DashboardPage implements OnInit {
  private readonly api = inject(ApiService);
  protected readonly stats = signal<any | null>(null);

  ngOnInit(): void {
    this.api.getAdminStats().subscribe({
      next: (data) => this.stats.set(data),
      error: () => this.stats.set({ error: 'Failed to load stats. Ensure Flask is running and you are authenticated.' })
    });
  }
}

