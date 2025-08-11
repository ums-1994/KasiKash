import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  // Admin dashboard stats (requires session auth)
  getAdminStats(): Observable<any> {
    return this.http.get('/admin/api/dashboard/stats');
  }
}

