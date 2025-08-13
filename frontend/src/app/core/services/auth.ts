import { Injectable, inject } from '@angular/core';
import { Observable, of } from 'rxjs';
import { Api } from './api';

@Injectable({
  providedIn: 'root'
})
export class Auth {
  private readonly api = inject(Api);

  login(credentials: { email: string; password: string }): Observable<{ success: boolean; message?: string }> {
    return this.api.post<{ success: boolean; message?: string }>(
      '/login_validation',
      credentials,
      { 'Content-Type': 'application/json' }
    );
  }

  logout(): Observable<void> {
    return this.api.post<void>('/logout', {});
  }

  isAuthenticated(): Observable<boolean> {
    // TODO: Wire to a real session endpoint
    return of(false);
  }
}
